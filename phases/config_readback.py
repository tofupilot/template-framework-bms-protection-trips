from utils.recipe import CELL_COUNT, IDLE_MV


def config_readback(measurements, bench, unit, log):
    """Setup: the protection block read bit-exact before any stimulus. A
    board that left programming with the OTP unwritten fails here in
    milliseconds, with no fixture time spent hunting trip points."""
    bench.set_all_cells_mv(IDLE_MV)
    bench.dut_clear_faults()
    measurements.protection_config = bench.dut_read_config()
    measurements.config_crc = bench.dut_config_crc()
    unit.metadata["config_crc"] = bench.dut_config_crc()
    log.info(f"Board {unit.serial_number}: config CRC {bench.dut_config_crc()}, {CELL_COUNT} cells at {IDLE_MV} mV")
