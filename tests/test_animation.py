from tibia_mirror.ui.base.animation import Tween, ease_out_cubic, lerp


def test_ease_out_cubic_endpoints():
    assert ease_out_cubic(0.0) == 0.0
    assert ease_out_cubic(1.0) == 1.0


def test_ease_out_cubic_starts_fast_and_is_monotonic():
    samples = [ease_out_cubic(i / 20) for i in range(21)]
    assert samples == sorted(samples)
    assert ease_out_cubic(0.5) > 0.5  # most of the change happens early


def test_lerp():
    assert lerp(0.5, 0.0, 0.0) == 0.5
    assert lerp(0.5, 0.0, 1.0) == 0.0
    assert lerp(0.0, 1.0, 0.25) == 0.25


def test_zero_duration_jumps_to_the_end_at_once():
    steps, done = [], []
    # No widget: an instant tween must never schedule a frame.
    Tween(None, 0.0, 1.0, 0, steps.append, lambda: done.append(True))
    assert steps == [1.0]
    assert done == [True]
