import math

from utils.recipe import CONFIG, NTC_BETA_K, NTC_POINTS_C, NTC_R25_OHM, NTC_SWEEP_OHM


def ntc_ohm(temp_c):
    return NTC_R25_OHM * math.exp(NTC_BETA_K * (1.0 / (temp_c + 273.15) - 1.0 / 298.15))


def otp_thermistor(measurements, bench, log):
    """Over-temperature by resistance substitution on the TS pin, at two
    points: every 10 kOhm NTC reads 25 C at 25 C, only a hot point tells a
    B=3435 reel from a B=3977 one. Then a sweep down to the OTD trip, and
    an open thermistor that must raise a fault, not read a temperature."""
    bench.dut_clear_faults()
    reported = {}
    for t in NTC_POINTS_C:
        bench.set_ts_ohm(ntc_ohm(t))
        reported[t] = bench.dut_read_temperature_c()
        log.info(f"TS at {ntc_ohm(t):.0f} ohm ({t:.0f} C by the B={NTC_BETA_K:.0f} model): DUT reports {reported[t]:.1f} C")
    measurements.temp_at_25c = reported[25.0]
    measurements.temp_at_60c = reported[60.0]

    bench.dut_clear_faults()
    trip_c = None
    ohm = NTC_SWEEP_OHM[0]
    while ohm >= NTC_SWEEP_OHM[1]:
        bench.set_ts_ohm(ohm)
        if bench.otd_tripped():
            trip_c = NTC_BETA_K / (NTC_BETA_K / 298.15 + math.log(ohm / NTC_R25_OHM)) - 273.15
            break
        ohm -= NTC_SWEEP_OHM[2]
    measurements.otd_trip_c = float(trip_c)
    log.info(f"OTD trips at {ohm} ohm = {trip_c:.1f} C against {CONFIG['otd_c']} C")

    bench.dut_clear_faults()
    bench.open_ts()
    measurements.ts_open_flagged = bench.ts_open_flagged()
    bench.set_ts_ohm(NTC_R25_OHM)
    bench.dut_clear_faults()
