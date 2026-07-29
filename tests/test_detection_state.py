from vireo.detection_state import Detection, DetectionState


def test_new_object_is_announced_once_while_active():
    state = DetectionState(absence_threshold=0.4)
    first = state.update([Detection("person", 0.9)], now=1.0)
    second = state.update([Detection("person", 0.95)], now=1.1)

    assert [item.label for item in first] == ["person"]
    assert second == []


def test_object_can_be_announced_after_real_absence():
    state = DetectionState(absence_threshold=0.4)
    state.update([Detection("chair", 0.8)], now=1.0)
    state.update([], now=1.2)
    too_soon = state.update([Detection("chair", 0.85)], now=1.3)
    state.update([], now=1.8)
    after_cooldown = state.update([Detection("chair", 0.9)], now=1.9)

    assert too_soon == []
    assert [item.label for item in after_cooldown] == ["chair"]


def test_strongest_duplicate_detection_is_kept():
    state = DetectionState()
    announcements = state.update(
        [Detection("bottle", 0.55), Detection("bottle", 0.91)],
        now=1.0,
    )
    assert announcements == [Detection("bottle", 0.91)]
