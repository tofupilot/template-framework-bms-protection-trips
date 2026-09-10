from utils.recipe import IDLE_MV


def restore(measurements, bench, log):
    """Teardown: stimulus off, cells at idle, faults cleared, and the config
    CRC read again so a threshold the test lowered can never ship lowered."""
    bench.inject_mv(0)
    bench.set_all_cells_mv(IDLE_MV)
    bench.dut_clear_faults()
    measurements.faults_after_restore = bench.dut_read_faults()
    measurements.config_crc_after = bench.dut_config_crc()
    log.info(f"Restored: config CRC {bench.dut_config_crc()}, faults {bench.dut_read_faults()}")
