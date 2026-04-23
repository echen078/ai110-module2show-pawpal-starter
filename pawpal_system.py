"""
PawPal+ logic layer — all backend classes live here.
"""

from dataclasses import dataclass, field, replace


@dataclass
class Task:
    name: str
    category: str          # "walk" | "feed" | "meds" | "grooming" | "enrichment"
    duration_minutes: int
    priority: int          # 1 (low) – 5 (high)
    completed: bool = False
    start_time: int | None = None    # minutes from midnight (e.g. 480 = 8:00 AM); None = floating
    recurrence: str | None = None    # "daily" | None

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self) -> "Task | None":
        """Return a fresh uncompleted copy for the next cycle, or None if non-recurring."""
        if self.recurrence is None:
            return None
        return replace(self, completed=False)

    def fits_in(self, remaining_minutes: int) -> bool:
        """Return True if this task's duration is within the remaining time budget."""
        return self.duration_minutes <= remaining_minutes

    @property
    def end_time(self) -> int | None:
        """Return the minute at which this pinned task ends, or None if floating."""
        if self.start_time is None:
            return None
        return self.start_time + self.duration_minutes


@dataclass
class Pet:
    name: str
    species: str
    age: int               # years
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, name: str) -> None:
        """Remove all tasks whose name matches the given string."""
        self.tasks = [t for t in self.tasks if t.name != name]

    def complete_task(self, name: str) -> "Task | None":
        """Mark a task done; if recurring, append its next occurrence and return it."""
        for task in self.tasks:
            if task.name == name and not task.completed:
                task.mark_complete()
                next_task = task.next_occurrence()
                if next_task is not None:
                    self.tasks.append(next_task)
                return next_task
        return None

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's household."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove all pets whose name matches the given string."""
        self.pets = [p for p in self.pets if p.name != name]

    def get_all_tasks(self) -> list[Task]:
        """Return a flat list of every task across all this owner's pets."""
        return [task for pet in self.pets for task in pet.get_tasks()]


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.available_minutes = owner.available_minutes
        self._skipped: list[Task] = []
        self._conflicts: list[str] = []

    def generate_plan(self) -> list[Task]:
        """Build and return the day's task list sorted by priority and filtered by time."""
        all_tasks = self.owner.get_all_tasks()
        sorted_tasks = self._sort_by_priority(all_tasks)
        plan = self._filter_by_time(sorted_tasks)
        self._conflicts = self.detect_conflicts(plan)
        return plan

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return warning strings for any pairs of pinned tasks whose time windows overlap."""
        pinned = [t for t in tasks if t.start_time is not None]
        warnings: list[str] = []
        for i, a in enumerate(pinned):
            for b in pinned[i + 1:]:
                if self._overlaps(a, b):
                    warnings.append(
                        f"⚠ Conflict: '{a.name}' ({_fmt_time(a.start_time)}–{_fmt_time(a.end_time)}) "
                        f"overlaps with '{b.name}' ({_fmt_time(b.start_time)}–{_fmt_time(b.end_time)})"
                    )
        return warnings

    def explain_plan(self, plan: list[Task]) -> str:
        """Return a human-readable summary of scheduled, skipped, and conflicting tasks."""
        lines: list[str] = []

        total_scheduled = sum(t.duration_minutes for t in plan)
        lines.append(
            f"Scheduled {len(plan)} task(s) using {total_scheduled} of "
            f"{self.available_minutes} available minutes.\n"
        )

        if plan:
            lines.append("Included:")
            for t in plan:
                time_note = f" @ {_fmt_time(t.start_time)}" if t.start_time is not None else ""
                lines.append(
                    f"  ✓ {t.name} ({t.category}, {t.duration_minutes} min, priority {t.priority}{time_note})"
                )

        if self._skipped:
            lines.append("\nSkipped (not enough time remaining):")
            for t in self._skipped:
                lines.append(
                    f"  ✗ {t.name} ({t.category}, {t.duration_minutes} min, priority {t.priority})"
                )

        if self._conflicts:
            lines.append("\nConflicts detected:")
            for warning in self._conflicts:
                lines.append(f"  {warning}")

        return "\n".join(lines)

    def _sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return a new list sorted highest-priority first.

        Note: operator.attrgetter('priority') is more "Pythonic" but the lambda
        is kept here because it reads as plain English for this audience.
        """
        return sorted(tasks, key=lambda t: t.priority, reverse=True)

    def _filter_by_time(self, tasks: list[Task]) -> list[Task]:
        """Greedily include tasks in priority order while the time budget allows."""
        remaining = self.available_minutes
        included: list[Task] = []
        self._skipped = []

        for task in tasks:
            if task.fits_in(remaining):
                included.append(task)
                remaining -= task.duration_minutes
            else:
                self._skipped.append(task)

        return included

    @staticmethod
    def _overlaps(a: Task, b: Task) -> bool:
        """Return True if two pinned tasks' time windows intersect."""
        # Standard interval-overlap test: [a.start, a.end) ∩ [b.start, b.end) ≠ ∅
        return a.start_time < b.end_time and b.start_time < a.end_time


def _fmt_time(minutes: int | None) -> str:
    """Convert an absolute minute value to HH:MM, or '?' if None."""
    if minutes is None:
        return "?"
    return f"{minutes // 60:02d}:{minutes % 60:02d}"
