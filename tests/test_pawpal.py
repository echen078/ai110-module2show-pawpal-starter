import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# --- fixtures ---------------------------------------------------------------

@pytest.fixture
def sample_task():
    return Task(name="Morning walk", category="walk", duration_minutes=30, priority=5)


@pytest.fixture
def sample_pet():
    return Pet(name="Luna", species="dog", age=3)


@pytest.fixture
def sample_owner():
    return Owner(name="Alex", available_minutes=60)


# --- Task tests -------------------------------------------------------------

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


# --- Pet tests --------------------------------------------------------------

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


# --- Owner tests ------------------------------------------------------------

def test_get_all_tasks_aggregates_across_pets(sample_owner):
    dog = Pet("Luna", "dog", 3)
    cat = Pet("Mochi", "cat", 5)
    dog.add_task(Task("Walk", "walk", 30, priority=5))
    cat.add_task(Task("Feed", "feed", 10, priority=5))
    sample_owner.add_pet(dog)
    sample_owner.add_pet(cat)
    assert len(sample_owner.get_all_tasks()) == 2


# --- Scheduler tests --------------------------------------------------------

def test_scheduler_respects_time_budget():
    owner = Owner("Alex", available_minutes=30)
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Walk",  "walk", 30, priority=5))   # fits exactly
    pet.add_task(Task("Fetch", "enrichment", 20, priority=3))  # would exceed budget
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    assert len(plan) == 1
    assert plan[0].name == "Walk"


def test_scheduler_orders_by_priority():
    owner = Owner("Alex", available_minutes=60)
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Low prio",  "enrichment", 10, priority=1))
    pet.add_task(Task("High prio", "walk",        10, priority=5))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    assert plan[0].name == "High prio"
    assert plan[1].name == "Low prio"


def test_skipped_tasks_tracked(sample_owner):
    pet = Pet("Luna", "dog", 3)
    pet.add_task(Task("Walk",  "walk", 55, priority=5))
    pet.add_task(Task("Fetch", "enrichment", 20, priority=3))  # won't fit after walk
    sample_owner.add_pet(pet)

    scheduler = Scheduler(sample_owner)
    scheduler.generate_plan()

    assert len(scheduler._skipped) == 1
    assert scheduler._skipped[0].name == "Fetch"
