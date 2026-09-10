import numpy as np

from phases.ovp_trip import find_trip
from utils.recipe import CELL_COUNT, CONFIG, IDLE_MV, UV_SEARCH


def uvp_trip(measurements, bench, log):
    """Under-voltage trip point and delay, one channel lowered at a time.
    Lowering all sixteen together trips the stack shutdown and the station
    reports a comms timeout instead of a UV result."""
    trip = np.zeros(CELL_COUNT)
    delay = np.zeros(CELL_COUNT)
    for ch in range(1, CELL_COUNT + 1):
        trip[ch - 1] = find_trip(bench, ch, *UV_SEARCH, rising=False)
        delay[ch - 1] = bench.alert_delay_ms("uv")
        bench.set_cell_mv(ch, IDLE_MV)
    bench.dut_clear_faults()
    dev = trip - CONFIG["uv_mv"]

    measurements.uv_trips.x_axis = list(range(1, CELL_COUNT + 1))
    measurements.uv_trips.y_axis.trip = trip.round(1).tolist()
    measurements.uv_trips.y_axis.trip.aggregations.max_dev_mv = float(dev.max())
    measurements.uv_trips.y_axis.trip.aggregations.min_dev_mv = float(dev.min())
    measurements.uv_trips.y_axis.delay = delay.tolist()
    measurements.uv_trips.y_axis.delay.aggregations.max_ms = float(delay.max())
    log.info(f"UV trips {trip.min():.0f}..{trip.max():.0f} mV against {CONFIG['uv_mv']}, delay up to {delay.max():.1f} ms")
