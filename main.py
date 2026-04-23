"""
Demo script — creates sample data and prints today's schedule.
Run with: python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler

MINUTES_8AM = 8 * 60   # 480


def print_schedule(plan: list[Task], explanation: str, conflicts: list[str]) -> None:
    width = 56
    print("=" * width)
    print(" 🐾  PawPal+ — Today's Schedule")
    print("=" * width)

    if not plan:
        print("  No tasks could be scheduled today.")
    else:
        for i, task in enumerate(plan, start=1):
            status = "✓" if task.completed else "○"
            time_tag = f"@{task.start_time//60:02d}:{task.start_time%60:02d} " if task.start_time is not None else ""
            print(
                f"  {i}. [{status}] {time_tag}{task.name:<22} "
                f"{task.duration_minutes:>3} min  (priority {task.priority})"
            )

    if conflicts:
        print()
        print("  ── Conflict warnings ──")
        for warning in conflicts:
            print(f"  {warning}")

    print("-" * width)
    print(explanation)
    print("=" * width)


def main() -> None:
    # --- Owner setup ---
    alex = Owner(name="Alex", available_minutes=90)

    # --- Pets ---
    luna  = Pet(name="Luna",  species="dog", age=3)
    mochi = Pet(name="Mochi", species="cat", age=5)

    # --- Luna's tasks ---
    luna.add_task(Task("Morning walk",   "walk",       30, priority=5))
    luna.add_task(Task("Breakfast",      "feed",       10, priority=5))
    # Pinned at 8:00 AM — will conflict with Mochi's pinned task below
    luna.add_task(Task("Heartworm meds", "meds",        5, priority=4, start_time=MINUTES_8AM))
    luna.add_task(Task("Fetch session",  "enrichment", 20, priority=3))

    # --- Mochi's tasks ---
    mochi.add_task(Task("Breakfast",      "feed",       10, priority=5))
    mochi.add_task(Task("Flea treatment", "meds",        5, priority=4))
    # Also pinned at 8:00 AM — overlaps with Luna's heartworm meds
    mochi.add_task(Task("Eye drops",      "meds",        5, priority=4, start_time=MINUTES_8AM))
    mochi.add_task(Task("Brush coat",     "grooming",   15, priority=2))

    alex.add_pet(luna)
    alex.add_pet(mochi)

    # --- Schedule ---
    scheduler = Scheduler(alex)
    plan      = scheduler.generate_plan()
    conflicts = scheduler._conflicts
    explanation = scheduler.explain_plan(plan)

    print_schedule(plan, explanation, conflicts)


if __name__ == "__main__":
    main()
