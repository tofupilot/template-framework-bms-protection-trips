import numpy as np

from utils.recipe import CELL_COUNT, CONFIG, IDLE_MV, OV_SEARCH, SEARCH_RESOLUTION_MV


def find_trip(bench, channel, lo, hi, rising):
    """Binary search on one channel: seven steps from a 300 mV window to
    1 mV. The other fifteen channels stay at idle the whole time."""
    while hi - lo > SEARCH_RESOLUTION_MV:
        mid = 0.5 * (lo + hi)
        bench.dut_clear_faults()
        bench.set_cell_mv(channel, mid)
        tripped = bench.ov_tripped(channel) if rising else bench.uv_tripped(channel)
        if tripped:
            hi = mid if rising else hi
            lo = lo if rising else mid
        else:
            lo = mid if rising else lo
            hi = hi if rising else mid
    return 0.5 * (lo + hi)


def ovp_trip(measurements, bench, log):
    """Over-voltage trip point and delay on every channel, one channel
    raised at a time while the rest sit at 3.6 V."""
    trip = np.zeros(CELL_COUNT)
    delay = np.zeros(CELL_COUNT)
    for ch in range(1, CELL_COUNT + 1):
        trip[ch - 1] = find_trip(bench, ch, *OV_SEARCH, rising=True)
        delay[ch - 1] = bench.alert_delay_ms("ov")
        bench.set_cell_mv(ch, IDLE_MV)
    bench.dut_clear_faults()
    dev = trip - CONFIG["ov_mv"]

    measurements.ov_trips.x_axis = list(range(1, CELL_COUNT + 1))
    measurements.ov_trips.y_axis.trip = trip.round(1).tolist()
    measurements.ov_trips.y_axis.trip.aggregations.max_dev_mv = float(dev.max())
    measurements.ov_trips.y_axis.trip.aggregations.min_dev_mv = float(dev.min())
    measurements.ov_trips.y_axis.delay = delay.tolist()
    measurements.ov_trips.y_axis.delay.aggregations.max_ms = float(delay.max())
    worst = int(np.abs(dev).argmax()) + 1
    log.info(f"OV trips {trip.min():.0f}..{trip.max():.0f} mV against {CONFIG['ov_mv']}, worst channel {worst} at {dev[worst - 1]:+.0f} mV, delay up to {delay.max():.1f} ms")
