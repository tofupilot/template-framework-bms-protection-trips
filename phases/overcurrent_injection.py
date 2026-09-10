from utils.recipe import OCD_SWEEP_MV, SCD_OVERDRIVE_MV, SCD_SWEEP_MV


def overcurrent_injection(measurements, bench, log):
    """OCD1 and SCD thresholds by voltage injection across SRP-SRN: the
    comparators see a differential voltage and cannot tell a source from a
    shunt. Proves comparator, threshold config, fault path and FET drive;
    proves nothing about the shunt itself."""
    bench.dut_clear_faults()
    ocd_trip = None
    for mv in range(*OCD_SWEEP_MV):
        bench.inject_mv(mv)
        if bench.ocd1_tripped():
            ocd_trip = mv
            break
    ocd_delay = bench.alert_delay_ms("ocd1")
    bench.inject_mv(0)
    bench.dut_clear_faults()

    scd_trip = None
    for mv in range(*SCD_SWEEP_MV):
        bench.inject_mv(mv)
        if bench.scd_tripped():
            scd_trip = mv
            break
    bench.inject_mv(0)
    bench.dut_clear_faults()
    # Response time with a stated overdrive; without the overdrive the
    # number is not comparable to anything.
    bench.inject_mv(scd_trip + SCD_OVERDRIVE_MV)
    scd_us = bench.scd_response_us(SCD_OVERDRIVE_MV)
    gate_v = bench.dsg_gate_v()
    resets = bench.dut_reset_flags()
    bench.inject_mv(0)
    bench.dut_clear_faults()

    measurements.ocd1_trip_mv = float(ocd_trip)
    measurements.ocd1_delay_ms = ocd_delay
    measurements.scd_trip_mv = float(scd_trip)
    measurements.scd_response_us = scd_us
    measurements.dsg_gate_after_scd_v = gate_v
    measurements.reset_flags_after_scd = resets
    log.info(f"OCD1 at {ocd_trip} mV in {ocd_delay:.1f} ms, SCD at {scd_trip} mV, gate off in {scd_us:.1f} us at +{SCD_OVERDRIVE_MV} mV overdrive, resets {resets}")
