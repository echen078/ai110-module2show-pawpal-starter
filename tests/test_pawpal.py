import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_task():
    return Task(name="Morning walk", category="walk", duration_minutes=30, priority=5)


@pytest.fixture
def sample_pet():
    return Pet(name="Luna", species="dog", age=3)


@pytest.fixture
def sample_owner():
    return Owner(name="Alex", available_minutes=60)


# ---------------------------------------------------------------------------
# Task — completion
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status(sample_task):
    assert sample_task.completed is False
    sample_task.mark_complete()
    assert sample_task.completed is True


def test_fits_in_true_when_enough_time(sample_task):
    assert sample_task.fits_in(30) is True
    assert sample_task.fits_in(60) is True


def test_fits_in_false_when_not_enough_time(sample_task):
    assert sample_task.fits_in(29) is False
    assert sample_task.fits_in(0) is False


# ---------------------------------------------------------------------------
# Task — recurrence
# ---------------------------------------------------------------------------

def test_recurring_task_produces_next_occurrence():
    task = Task("Feed", "feed", 10, priority=5, recurrence="daily")
    task.mark_complete()
    next_task = task.next_occurrence()
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.name == "Feed"
    assert next_task.recurrence == "daily"


def test_non_recurring_task_returns_none_for_next_occurrence(sample_task):
    sample_task.mark_complete()
    assert sample_task.next_occurrence() is None


def test_next_occurrence_preserves_all_attributes():
    task = Task("Meds", "meds", 5, priority=4, start_time=480, recurrence="daily")
    next_task = task.next_occurrence()
    assert next_task.duration_minutes == 5
    assert next_task.priority == 4
    assert next_task.start_time == 480
    assert next_task.recurrence == "daily"


# ---------------------------------------------------------------------------
# Pet — task management and recurrence
# ---------------------------------------------------------------------------

def test_add_task_increases_count(sample_pet, sample_task):
    assert len(sample_pet.get_tasks()) == 0
    sample_pet.add_task(sample_task)
    assert len(sample_pet.get_tasks()) == 1


def test_add_multiple_tasks(sample_pet):
    sample_pet.add_task(Task("Feed", "feed", 10, priority=5))
    sample_pet.add_task(Task("Meds", "meds", 5, priority=4))
    assert len(sample_pet.get_tasks()) == 2


def test_remove_task_by_name(sample_pet, sample_task):
    sample_pet.add_task(sample_task)
    sample_pet.remove_task("Morning walk")
    assert len(sample_pet.get_tasks()) == 0


def test_complete_task_daily_appends_new_copy(sample_pet):
    """Completing a recurring daily task should grow the pet's task list by 1."""
    task = Task("Evening feed", "feed", 10, priority=5, recurrence="daily")
    sample_pet.add_task(task)
    assert len(sample_pet.get_tasks()) == 1

    result = sample_pet.complete_task("Evening feed")

    assert result is not None
    tasks = sample_pet.get_tasks()
    assert len(tasks) == 2                  # original + new occurrence
    assert tasks[0].completed is True       # original is done
    assert tasks[1].completed is False      # new copy is fresh
    assert tasks[1].name == "Evening feed"


def test_complete_task_non_recurring_does_not_append(sample_pet, sample_task):
    """Completing a one-off task should NOT add another task."""
    sample_pet.add_task(sample_task)
    result = sample_pet.complete_task("Morning walk")
    assert result is None
    assert len(sample_pet.get_tasks()) == 1


def test_complete_task_already_completed_is_ignored(sample_pet):
    """Calling complete_task on an already-done task has no effect."""
    task = Task("Feed", "feed", 10, priority=5, recurrence="daily")
    task.mark_complete()
    sample_pet.add_task(task)
    result = sample_pet.complete_task("Feed")   # task is already done
    assert result is None
    assert len(sample_pet.get_tasks()) == 1     # no new task appended


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

def test_get_all_tasks_aggregates_across_pets(sample_owner):
    dog = Pet("Luna", "dog", 3)
    cat = Pet("Mochi", "cat", 5)
    dog.add_task(Task("Walk", "walk", 30, priority=5))
    cat.add_task(Task("Feed", "feed", 10, priority=5))
    sample_owner.add_pet(dog)
    sample_owner.add_pet(cat)
    assert len(sample_owner.get_all_tasks()) == 2


def test_owner_with_no_pets_returns_empty_tasks(sample_owner):
    assert sample_owner.get_all_tasks() == []


# ---------------------------------------------------------------------------
# Scheduler — sorting correctness
# ---------------------------------------------------------------------------

def test_sorting_correctness_full_priority_range():
    """Tasks added in arbitrary order must come back sorted 5→4→3→2→1."""
    owner = Owner("Alex", available_minutes=300)
    pet = Pet("Luna", "dog", 3)
    for name, priority in [("C", 3), ("A", 5), ("E", 1), ("B", 4), ("D", 2)]:
        pet.add_task(Task(name, "walk", 10, priority=priority))
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_plan()
    priorities = [t.priority for t in plan]
    assert priorities == sorted(priorities, reverse=True)


def test_equal_priority_tasks_all_appear(sample_owner):
    """When two tasks share the same priority, both are included if time allows."""
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Walk", "walk", 10, priority=3))
    pet.add_task(Task("Feed", "feed", 10, priority=3))
    sample_owner.add_pet(pet)

    plan = Scheduler(sample_owner).generate_plan()
    assert len(plan) == 2


# ---------------------------------------------------------------------------
# Scheduler — time budget
# ---------------------------------------------------------------------------

def test_scheduler_respects_time_budget():
    owner = Owner("Alex", available_minutes=30)
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Walk",  "walk",       30, priority=5))  # fits exactly
    pet.add_task(Task("Fetch", "enrichment", 20, priority=3))  # exceeds remaining budget
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_plan()
    assert len(plan) == 1
    assert plan[0].name == "Walk"


def test_task_exactly_fills_budget_nothing_left():
    owner = Owner("Alex", available_minutes=20)
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Walk", "walk", 20, priority=5))
    pet.add_task(Task("Feed", "feed", 5,  priority=4))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    assert len(plan) == 1
    assert len(scheduler._skipped) == 1


def test_zero_budget_skips_all_tasks():
    owner = Owner("Alex", available_minutes=0)
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Walk", "walk", 30, priority=5))
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_plan()
    assert plan == []


def test_empty_pet_produces_empty_plan(sample_owner):
    sample_owner.add_pet(Pet("Empty", "dog", 1))
    plan = Scheduler(sample_owner).generate_plan()
    assert plan == []


def test_skipped_tasks_tracked(sample_owner):
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Walk",  "walk",       55, priority=5))
    pet.add_task(Task("Fetch", "enrichment", 20, priority=3))
    sample_owner.add_pet(pet)

    scheduler = Scheduler(sample_owner)
    scheduler.generate_plan()
    assert len(scheduler._skipped) == 1
    assert scheduler._skipped[0].name == "Fetch"


# ---------------------------------------------------------------------------
# Scheduler — conflict detection
# ---------------------------------------------------------------------------

def test_conflict_detected_for_same_start_time(sample_owner):
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Meds A", "meds", 5, priority=5, start_time=480))
    pet.add_task(Task("Meds B", "meds", 5, priority=5, start_time=480))
    sample_owner.add_pet(pet)

    scheduler = Scheduler(sample_owner)
    scheduler.generate_plan()
    assert len(scheduler._conflicts) == 1
    assert "Meds A" in scheduler._conflicts[0]
    assert "Meds B" in scheduler._conflicts[0]


def test_conflict_detected_for_overlapping_windows(sample_owner):
    """Task A: 08:00–08:30, Task B: 08:15–08:45 — they overlap."""
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Walk",  "walk", 30, priority=5, start_time=480))
    pet.add_task(Task("Fetch", "enrichment", 30, priority=4, start_time=495))
    sample_owner.add_pet(pet)

    scheduler = Scheduler(sample_owner)
    scheduler.generate_plan()
    assert len(scheduler._conflicts) == 1


def test_no_conflict_for_adjacent_tasks(sample_owner):
    """Task A ends exactly when Task B starts — no overlap."""
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Walk", "walk", 30, priority=5, start_time=480))   # 08:00–08:30
    pet.add_task(Task("Feed", "feed", 10, priority=4, start_time=510))   # 08:30–08:40
    sample_owner.add_pet(pet)

    scheduler = Scheduler(sample_owner)
    scheduler.generate_plan()
    assert scheduler._conflicts == []


def test_no_conflict_for_floating_tasks(sample_owner):
    """Floating tasks (no start_time) are never flagged as conflicts."""
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Walk", "walk", 30, priority=5))
    pet.add_task(Task("Feed", "feed", 10, priority=4))
    sample_owner.add_pet(pet)

    scheduler = Scheduler(sample_owner)
    scheduler.generate_plan()
    assert scheduler._conflicts == []
