"""
Demo script — creates sample data and prints today's schedule.
Run with: python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def print_schedule(plan: list[Task], explanation: str) -> None:
    width = 52
    print("=" * width)
    print(" 🐾  PawPal+ — Today's Schedule")
    print("=" * width)

    if not plan:
        print("  No tasks could be scheduled today.")
    else:
        for i, task in enumerate(plan, start=1):
            status = "✓" if task.completed else "○"
            print(
                f"  {i}. [{status}] {task.name:<22} "
                f"{task.duration_minutes:>3} min  (priority {task.priority})"
            )

    print("-" * width)
    print(explanation)
    print("=" * width)


def main() -> None:
    # --- Owner setup ---
    alex = Owner(name="Alex", available_minutes=90)

    # --- Pets ---
    luna = Pet(name="Luna", species="dog", age=3)
    mochi = Pet(name="Mochi", species="cat", age=5)

    # --- Luna's tasks ---
    luna.add_task(Task("Morning walk",    "walk",       30, priority=5))
    luna.add_task(Task("Breakfast",       "feed",       10, priority=5))
    luna.add_task(Task("Heartworm meds",  "meds",        5, priority=4))
    luna.add_task(Task("Fetch session",   "enrichment", 20, priority=3))

    # --- Mochi's tasks ---
    mochi.add_task(Task("Breakfast",      "feed",       10, priority=5))
    mochi.add_task(Task("Flea treatment", "meds",        5, priority=4))
    mochi.add_task(Task("Brush coat",     "grooming",   15, priority=2))
    mochi.add_task(Task("Puzzle feeder",  "enrichment", 10, priority=2))

    alex.add_pet(luna)
    alex.add_pet(mochi)

    # --- Schedule ---
    scheduler = Scheduler(alex)
    plan = scheduler.generate_plan()
    explanation = scheduler.explain_plan(plan)

    print_schedule(plan, explanation)


if __name__ == "__main__":
    main()
