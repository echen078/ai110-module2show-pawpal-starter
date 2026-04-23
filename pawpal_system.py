"""
PawPal+ logic layer — all backend classes live here.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    name: str
    category: str          # e.g. "walk", "feed", "meds", "grooming", "enrichment"
    duration_minutes: int
    priority: int          # 1 (low) – 5 (high)
    completed: bool = False

    def mark_complete(self) -> None:
        self.completed = True

    def fits_in(self, remaining_minutes: int) -> bool:
        """Return True if this task can fit within the remaining time budget."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int               # years
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, name: str) -> None:
        pass

    def get_tasks(self) -> list[Task]:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, name: str) -> None:
        pass

    def get_all_tasks(self) -> list[Task]:
        """Aggregate tasks from every pet this owner has."""
        pass


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.available_minutes = owner.available_minutes
        self._skipped: list[Task] = []   # populated by _filter_by_time; read by explain_plan

    def generate_plan(self) -> list[Task]:
        """Return an ordered list of tasks that fit within the time budget."""
        pass

    def explain_plan(self, plan: list[Task]) -> str:
        """Return a plain-language explanation of why tasks were included or skipped."""
        pass

    def _sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted highest priority first."""
        pass

    def _filter_by_time(self, tasks: list[Task]) -> list[Task]:
        """Greedily include tasks while remaining time allows."""
        pass
