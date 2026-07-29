"""Pure detection-state logic shared by the Hailo callback and tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float


@dataclass
class DetectionState:
    """Track object arrivals and departures without frame-level announcement spam.

    An object is announced when it is not active and either has never been seen or
    has remained absent for at least ``absence_threshold`` seconds.
    """

    absence_threshold: float = 0.4
    active_objects: dict[str, float] = field(default_factory=dict)
    last_removed: dict[str, float] = field(default_factory=dict)

    def update(self, detections: Iterable[Detection], now: float) -> list[Detection]:
        strongest_by_label: dict[str, Detection] = {}
        for detection in detections:
            current = strongest_by_label.get(detection.label)
            if current is None or detection.confidence > current.confidence:
                strongest_by_label[detection.label] = detection

        frame_labels = set(strongest_by_label)
        announcements: list[Detection] = []

        for label, detection in strongest_by_label.items():
            was_gone_long_enough = (
                label not in self.active_objects
                and (
                    label not in self.last_removed
                    or now - self.last_removed[label] >= self.absence_threshold
                )
            )
            if was_gone_long_enough:
                announcements.append(detection)
            self.active_objects[label] = now

        for label, last_seen in list(self.active_objects.items()):
            if label not in frame_labels and now - last_seen >= self.absence_threshold:
                del self.active_objects[label]
                self.last_removed[label] = last_seen

        return announcements
