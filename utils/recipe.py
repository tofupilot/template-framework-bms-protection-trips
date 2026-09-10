"""Protection recipe for a 16S BMS on a BQ76952-class AFE: the released
configuration the board must carry, the stimulus used to find each trip
point, and the NTC model the temperature checks are computed with.

Limits derive from the AFE datasheet, not from a standard: OV/UV threshold
accuracy is +-25 mV over -40..85 C in the 3.0-5.0 V band, widened by the
simulator; OC accuracy is +-5 mV in the 56-100 mV band; SCD is +-20 %; the
delay quantum is 3.3 ms. The NTC is a 10 kOhm B=3435 part (Murata
NCP18XH103F); a B=3977 part under the same model reads 5 K low at 60 C."""

CELL_COUNT = 16
IDLE_MV = 3600

# Released protection configuration, read back bit-exact in setup.
CONFIG = {
    "ov_mv": 4250, "ov_delay_ms": 100,
    "uv_mv": 2800, "uv_delay_ms": 100,
    "ocd1_mv": 60, "ocd1_delay_ms": 40,
    "scd_mv": 200, "scd_delay_us": 15,
    "otd_c": 60,
}
CONFIG_CRC = "0x3A7F"

# Binary search windows around the settings, in mV.
OV_SEARCH = (4100, 4400)
UV_SEARCH = (2650, 2950)
SEARCH_RESOLUTION_MV = 1.0

# Sense-resistor voltage injection at the AFE's SRP/SRN filter side.
OCD_SWEEP_MV = (40, 90, 1)  # start, stop, step
SCD_SWEEP_MV = (150, 260, 5)
SCD_OVERDRIVE_MV = 25  # response time is stated with this overdrive

# NTC model and the two temperature points, resistance in ohm.
NTC_R25_OHM = 10000.0
NTC_BETA_K = 3435.0
NTC_POINTS_C = [25.0, 60.0]
NTC_SWEEP_OHM = (4000, 2000, 25)  # start, stop, step, down toward the OTD trip
