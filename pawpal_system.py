"""
PawPal+ logic layer — all backend classes live here.
"""

from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    category: str          # "walk" | "feed" | "meds" | "grooming" | "enrichment"
    duration_minutes: int
    priority: int          # 1 (low) – 5 (high)
    completed: bool = False

    def mark_complete(self) -> None:
        self.completed = True

    def fits_in(self, remaining_minutes: int) -> bool:
        return self.duration_minutes <= remaining_minutes


@dataclass
class Pet:
    name: str
    species: str
    age: int               # years
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, name: str) -> None:
        self.tasks = [t for t in self.tasks if t.name != name]

    def get_tasks(self) -> list[Task]:
        return list(self.tasks)


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        self.pets = [p for p in self.pets if p.name != name]

    def get_all_tasks(self) -> list[Task]:
        """Aggregate tasks from every pet this owner has."""
        return [task for pet in self.pets for task in pet.get_tasks()]


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.available_minutes = owner.available_minutes
        self._skipped: list[Task] = []

    def generate_plan(self) -> list[Task]:
        """Return priority-sorted tasks that fit within the daily time budget."""
        all_tasks = self.owner.get_all_tasks()
        sorted_tasks = self._sort_by_priority(all_tasks)
        plan = self._filter_by_time(sorted_tasks)
        return plan

    def explain_plan(self, plan: list[Task]) -> str:
        lines: list[str] = []

        total_scheduled = sum(t.duration_minutes for t in plan)
        lines.append(
            f"Scheduled {len(plan)} task(s) using {total_scheduled} of "
            f"{self.available_minutes} available minutes.\n"
        )

        if plan:
            lines.append("Included:")
            for t in plan:
                lines.append(
                    f"  ✓ {t.name} ({t.category}, {t.duration_minutes} min, priority {t.priority})"
                )

        if self._skipped:
            lines.append("\nSkipped (not enough time remaining):")
            for t in self._skipped:
                lines.append(
                    f"  ✗ {t.name} ({t.category}, {t.duration_minutes} min, priority {t.priority})"
                )

        return "\n".join(lines)

    def _sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        return sorted(tasks, key=lambda t: t.priority, reverse=True)

    def _filter_by_time(self, tasks: list[Task]) -> list[Task]:
        """Greedy inclusion: take each task in priority order if it fits."""
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
