from tibia_mirror.geometry import (
    Rect,
    clamp_box,
    clamp_rect,
    fit_panel_size,
    magnifier_source,
    nudged_point,
    overlay_to_client,
    panel_geometry,
    place_beside,
    rect_from_drag,
    region_error,
    resize_around_center,
    scaled_size,
    scroll_fraction,
    scroll_thumb,
    slider_value,
    slider_x,
    zoom_for_width,
)


def test_rect_edges():
    r = Rect(10, 20, 30, 40)
    assert (r.right, r.bottom) == (40, 60)


def test_rect_from_drag_any_direction():
    expected = Rect(10, 20, 30, 40)
    assert rect_from_drag(10, 20, 40, 60) == expected
    assert rect_from_drag(40, 60, 10, 20) == expected
    assert rect_from_drag(40, 20, 10, 60) == expected


def test_overlay_to_client_primary_monitor():
    # Game client area starts 8px right / 31px down of the monitor origin.
    sel = Rect(100, 200, 50, 60)
    assert overlay_to_client(sel, (0, 0), (8, 31)) == Rect(92, 169, 50, 60)


def test_overlay_to_client_secondary_monitor_left_of_primary():
    # Monitor at negative x; borderless-fullscreen game fills it exactly.
    sel = Rect(100, 200, 50, 60)
    assert overlay_to_client(sel, (-1920, 0), (-1920, 0)) == Rect(100, 200, 50, 60)


def test_scaled_size_multiplies_and_keeps_a_pixel():
    assert scaled_size(100, 50, 2.0) == (200, 100)
    assert scaled_size(77, 83, 0.5) == (38, 42)
    assert scaled_size(3, 1, 0.25) == (1, 1)


def test_zoom_for_width_rounds_to_whole_percent_and_clamps():
    assert zoom_for_width(150, 100, (0.25, 4.0)) == 1.5
    assert zoom_for_width(133, 100, (0.25, 4.0)) == 1.33
    assert zoom_for_width(10, 100, (0.25, 4.0)) == 0.25
    assert zoom_for_width(900, 100, (0.25, 4.0)) == 4.0


def test_scroll_thumb_hidden_when_everything_fits():
    assert scroll_thumb(0.0, 1.0, 200, 24) is None


def test_scroll_thumb_proportional_size_and_ends():
    assert scroll_thumb(0.0, 0.5, 200, 24) == (0, 100)
    assert scroll_thumb(0.5, 1.0, 200, 24) == (100, 100)


def test_scroll_thumb_minimum_size_still_reaches_the_bottom():
    top, height = scroll_thumb(0.95, 1.0, 200, 24)  # 5% visible -> 10px, clamped
    assert height == 24
    assert top + height == 200


def test_scroll_fraction_inverts_scroll_thumb():
    for first in (0.0, 0.1, 0.37, 0.9):
        top, height = scroll_thumb(first, first + 0.1, 300, 24)
        assert abs(scroll_fraction(top, height, 300, 0.1) - first) < 0.01


def test_scroll_fraction_clamps_drag_past_the_ends():
    assert scroll_fraction(-50, 100, 200, 0.5) == 0.0
    assert scroll_fraction(500, 100, 200, 0.5) == 0.5


def test_slider_value_snaps_to_step_and_clamps():
    assert slider_value(0, 0, 100, 0.1, 1.0, 0.05) == 0.1
    assert slider_value(100, 0, 100, 0.1, 1.0, 0.05) == 1.0
    assert slider_value(-40, 0, 100, 0.1, 1.0, 0.05) == 0.1
    assert slider_value(500, 0, 100, 0.1, 1.0, 0.05) == 1.0
    assert slider_value(44.4, 0, 100, 0.1, 1.0, 0.05) == 0.5  # 0.4996 snaps to 0.5


def test_slider_x_inverts_slider_value():
    for value in (0.1, 0.25, 0.5, 0.85, 1.0):
        x = slider_x(value, 12, 212, 0.1, 1.0)
        assert slider_value(x, 12, 212, 0.1, 1.0, 0.05) == value


SCREEN = Rect(0, 0, 1000, 800)


def test_place_beside_prefers_the_right():
    assert place_beside(Rect(100, 100, 50, 40), 60, 30, SCREEN, 12) == (162, 100)


def test_place_beside_falls_back_to_the_left_at_the_right_edge():
    assert place_beside(Rect(900, 100, 80, 40), 60, 30, SCREEN, 12) == (828, 100)


def test_place_beside_falls_back_to_below_then_above():
    wide = Rect(0, 100, 1000, 40)  # no room on either side
    assert place_beside(wide, 60, 30, SCREEN, 12) == (0, 152)
    low_wide = Rect(0, 760, 1000, 40)
    assert place_beside(low_wide, 60, 30, SCREEN, 12) == (0, 718)


def test_place_beside_clamps_when_nothing_fits():
    full = Rect(0, 0, 1000, 800)
    assert place_beside(full, 60, 30, SCREEN, 12) == (940, 0)


def test_place_beside_respects_offset_bounds():
    monitor = Rect(-1920, 0, 1920, 1080)  # secondary monitor left of primary
    assert place_beside(Rect(-100, 50, 80, 40), 60, 30, monitor, 12) == (-172, 50)


def test_clamp_rect_moves_then_shrinks_into_the_area():
    assert clamp_rect(Rect(95, -5, 10, 10), 100, 100) == Rect(90, 0, 10, 10)
    assert clamp_rect(Rect(10, 10, 300, 20), 100, 100) == Rect(0, 10, 100, 20)


def test_resize_around_center_keeps_the_centre_and_stays_inside():
    assert resize_around_center(Rect(40, 40, 20, 20), 40, 10, 100, 100) == Rect(30, 45, 40, 10)
    assert resize_around_center(Rect(0, 0, 10, 10), 30, 30, 100, 100) == Rect(0, 0, 30, 30)


def test_clamp_box_moves_a_box_just_inside_bounds():
    bounds = Rect(0, 0, 1000, 800)
    assert clamp_box(500, 400, 100, 100, bounds) == (500, 400)
    assert clamp_box(950, -20, 100, 100, bounds) == (900, 0)
    assert clamp_box(-50, 790, 100, 100, bounds) == (0, 700)


def test_region_error_names_the_field_to_fix():
    assert region_error(10, 10, 100, 50, 800, 600, 5) is None
    assert region_error(0, 0, 4, 50, 800, 600, 5)[2] == "w"
    assert region_error(0, 0, 100, 601, 800, 600, 5)[2] == "h"
    message, values, field = region_error(750, 0, 100, 50, 800, 600, 5)
    assert (message.format(**values), field) == ("X must be 0 to 700 for this width", "x")
    assert region_error(0, -1, 100, 50, 800, 600, 5)[2] == "y"


def test_magnifier_source_centres_on_the_point_and_stays_inside():
    assert magnifier_source(100, 100, 25, 800, 600) == Rect(88, 88, 25, 25)
    assert magnifier_source(3, 598, 25, 800, 600) == Rect(0, 575, 25, 25)
    assert magnifier_source(-50, 900, 25, 800, 600) == Rect(0, 575, 25, 25)
    assert magnifier_source(5, 5, 25, 10, 8) == Rect(0, 0, 10, 8)


def test_rect_contains_its_pixels_only():
    r = Rect(10, 20, 30, 40)
    assert r.contains(10, 20) and r.contains(39, 59)
    assert not r.contains(40, 20) and not r.contains(10, 60) and not r.contains(9, 30)


def test_nudged_point_shifts_the_pointer_and_stays_on_the_overlay():
    assert nudged_point((100, 50), (0, 0), 1920, 1080) == (100, 50)
    assert nudged_point((100, 50), (-3, 10), 1920, 1080) == (97, 60)
    assert nudged_point((2, 1075), (-10, 10), 1920, 1080) == (0, 1079)


def test_panel_opens_centred_and_fits_the_screen():
    # A 1080p screen with a 40px taskbar: the full default height fits.
    assert panel_geometry((484, 996), 440, 40, Rect(0, 0, 1920, 1040)) == "484x996+718+2"
    # A 768px laptop screen: shorter, still whole on screen.
    assert panel_geometry((484, 960), 440, 48, Rect(0, 0, 1366, 728)) == "484x680+441+0"
    # Never below the minimum height.
    assert panel_geometry((484, 960), 440, 48, Rect(0, 0, 800, 400)).startswith("484x440+")
    # A work area that starts lower (taskbar on top) moves the panel with it.
    assert panel_geometry((484, 960), 440, 48, Rect(0, 40, 1920, 1040)) == "484x960+718+56"


def test_rect_contains_rect():
    area = Rect(0, 0, 1920, 1040)
    assert area.contains_rect(Rect(0, 0, 1920, 1040))
    assert area.contains_rect(Rect(100, 50, 500, 900))
    assert not area.contains_rect(Rect(-1, 50, 500, 900))  # past the left edge
    assert not area.contains_rect(Rect(1500, 50, 500, 900))  # past the right edge
    assert not area.contains_rect(Rect(100, 200, 500, 900))  # below the bottom


def test_remembered_panel_size_fits_the_screen_but_not_below_the_minimum():
    area = Rect(0, 0, 1920, 1040)
    assert fit_panel_size((625, 900), (625, 550), 50, area) == (625, 900)
    # Saved on a taller screen: as tall as this one allows under the title bar.
    assert fit_panel_size((625, 1300), (625, 550), 50, area) == (625, 990)
    assert fit_panel_size((2500, 900), (625, 550), 50, area) == (1920, 900)
    assert fit_panel_size((625, 900), (625, 550), 50, Rect(0, 0, 800, 400)) == (625, 550)
