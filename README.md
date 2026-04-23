# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

The scheduler goes beyond a simple to-do list in three ways:

- **Priority-first ordering** — tasks are sorted highest-to-lowest priority before the time filter runs, so the most important care items (medications, feeding) are always attempted before lower-priority ones (enrichment, grooming).
- **Greedy time filtering** — tasks are included in order until the owner's daily time budget is exhausted; anything that no longer fits is collected into a "skipped" list and surfaced in the plan explanation.
- **Conflict detection** — tasks can be pinned to an absolute start time (e.g., `start_time=480` for 8:00 AM). After the plan is built, the scheduler checks all pinned task pairs for time-window overlap using a standard interval intersection test and reports any conflicts as warnings — without crashing or silently dropping tasks.

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

**What the tests cover (25 tests across 4 groups):**

| Group | What's verified |
|---|---|
| Task completion | `mark_complete()` flips status; `fits_in()` respects exact boundaries |
| Recurrence | Daily tasks produce a fresh uncompleted copy; one-off tasks do not; attributes are preserved across occurrences |
| Pet management | `add_task`, `remove_task`, `complete_task` (including idempotency on already-completed tasks) |
| Scheduler — sorting | Priority order is correct across all 5 levels; equal-priority tasks both appear |
| Scheduler — time | Greedy inclusion respects the budget; a task that exactly fills the budget leaves nothing for the next; zero-budget skips all |
| Scheduler — conflicts | Overlapping pinned tasks are flagged; adjacent (non-overlapping) and floating tasks are not |
| Edge cases | Empty pet, owner with no pets, zero-minute budget |

**Confidence level: ★★★★☆**

The core scheduling behaviors (sorting, time filtering, conflict detection, recurrence) are well covered. The main gap is integration-level testing — the tests exercise each class in isolation, but do not test the full Streamlit UI flow end-to-end. Browser-level edge cases (e.g., adding a pet after the owner's time budget is already committed) are not yet tested.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
