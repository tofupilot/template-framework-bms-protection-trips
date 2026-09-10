"""BMS protection test bench (mock): cell simulator, sense-resistor voltage
injection source, programmable NTC resistor, and the DUT's UART, one plug
because the DUT reads what the bench forces.

Maps to a Chroma 87001-class cell simulator (16 ch, 1 ms settling), a
current-sensor simulation channel (Bloomy-style +-10 V, 16-bit, driven onto
the SRP/SRN filter side of the shunt), a Pickering 40-297A programmable
resistor on the TS pin, and the AFE's ALERT pin on a timer input. The mock
synthesizes a healthy board: every comparator inside the datasheet window,
one OV channel 18 mV low, the released config in OTP, an NTC of the right
B value. Swap for classes speaking SCPI and pyserial; the phases stay
unchanged.
"""

import math

import numpy as np

from utils.recipe import CELL_COUNT, CONFIG, CONFIG_CRC, NTC_BETA_K, NTC_R25_OHM


class ProtectionBench:
    LOW_OV_CHANNEL = 6  # zero-based; comparator 18 mV below setting, inside +-30

    def __init__(self, cell_count):
        self.cell_count = int(cell_count)
        self._rng = np.random.default_rng(76952)
        self._ov_trip = CONFIG["ov_mv"] + self._rng.normal(0.0, 7.0, self.cell_count)
        self._ov_trip[self.LOW_OV_CHANNEL] = CONFIG["ov_mv"] - 18.0
        self._uv_trip = CONFIG["uv_mv"] + self._rng.normal(0.0, 7.0, self.cell_count)
        self._ocd1_trip_mv = CONFIG["ocd1_mv"] + 1.4
        self._scd_trip_mv = CONFIG["scd_mv"] + 6.0
        self._ntc_beta = NTC_BETA_K  # a wrong reel would put 3977 here
        self._cells_mv = np.full(self.cell_count, 3600.0)
        self._inject_mv = 0.0
        self._ts_ohm = NTC_R25_OHM
        self._ts_open = False
        self._faults = {"ov": [], "uv": [], "ocd1": False, "scd": False, "otd": False, "ts_open": False}
        self._reset_flags = {"por": False, "wdt": False}
        # self.sim = pyvisa...; self.inj = pyvisa...; self.res = pyvisa...; self.dut = serial.Serial(...)
        print(f"Protection bench connected, {self.cell_count} channels at 3.6 V, injection 0 mV, TS 10.0 kOhm")

    # --- DUT configuration ------------------------------------------------

    def dut_read_config(self):
        """Protection registers decoded to engineering units, plus the CRC."""
        return dict(CONFIG)

    def dut_config_crc(self):
        return CONFIG_CRC

    def dut_clear_faults(self):
        self._faults = {"ov": [], "uv": [], "ocd1": False, "scd": False, "otd": False, "ts_open": False}

    def dut_read_faults(self):
        return {k: (list(v) if isinstance(v, list) else v) for k, v in self._faults.items()}

    def dut_reset_flags(self):
        """POR and watchdog flags: an SCD that reboots the device instead of
        tripping looks identical on the gate and different here."""
        return dict(self._reset_flags)

    def dut_read_temperature_c(self):
        """Temperature the DUT computes from the TS pin with its own B model."""
        if self._ts_open:
            return -40.0
        t_k = 1.0 / (1.0 / 298.15 + math.log(self._ts_ohm / NTC_R25_OHM) / self._ntc_beta)
        return round(t_k - 273.15 + self._rng.normal(0.0, 0.15), 2)

    # --- cell simulator ----------------------------------------------------

    def set_cell_mv(self, channel, mv):
        """One channel (1-based); the others stay where they are."""
        i = channel - 1
        self._cells_mv[i] = float(mv)
        if mv >= self._ov_trip[i] and channel not in self._faults["ov"]:
            self._faults["ov"].append(channel)
        if mv <= self._uv_trip[i] and channel not in self._faults["uv"]:
            self._faults["uv"].append(channel)

    def set_all_cells_mv(self, mv):
        self._cells_mv[:] = float(mv)

    def ov_tripped(self, channel):
        return channel in self._faults["ov"]

    def uv_tripped(self, channel):
        return channel in self._faults["uv"]

    def alert_delay_ms(self, kind):
        """Time from the stimulus edge to the ALERT pin, measured by the
        timer input: the configured delay plus the comparator's own latency."""
        base = CONFIG[f"{kind}_delay_ms"]
        return round(base + 1.2 + abs(self._rng.normal(0.0, 0.6)), 2)

    # --- current-sense injection --------------------------------------------

    def inject_mv(self, mv):
        """Differential voltage forced across SRP-SRN on the filter side."""
        self._inject_mv = float(mv)
        if mv >= self._ocd1_trip_mv:
            self._faults["ocd1"] = True
        if mv >= self._scd_trip_mv:
            self._faults["scd"] = True

    def ocd1_tripped(self):
        return self._faults["ocd1"]

    def scd_tripped(self):
        return self._faults["scd"]

    def scd_response_us(self, overdrive_mv):
        """Stimulus step to DSG gate falling, digitised at 100 MS/s. The
        comparator is sub-microsecond at 25 mV overdrive; the 100 ohm /
        0.1 uF input filter is what the number actually measures."""
        filter_us = 10.0 * math.log(1.0 + 4.0 * 25.0 / overdrive_mv)
        return round(CONFIG["scd_delay_us"] + filter_us + abs(self._rng.normal(0.0, 0.4)), 2)

    def dsg_gate_v(self):
        """DSG FET gate voltage: 12 V driven on, below 1 V off."""
        return 0.4 if (self._faults["scd"] or self._faults["ocd1"]) else 12.1

    # --- NTC substitution --------------------------------------------------

    def set_ts_ohm(self, ohm):
        self._ts_open = False
        self._ts_ohm = float(ohm)
        t = self.dut_read_temperature_c()
        if t >= CONFIG["otd_c"]:
            self._faults["otd"] = True

    def open_ts(self):
        self._ts_open = True
        self._faults["ts_open"] = True

    def otd_tripped(self):
        return self._faults["otd"]

    def ts_open_flagged(self):
        return self._faults["ts_open"]

    def __del__(self):
        print("Injection off, cells parked, bench released")
