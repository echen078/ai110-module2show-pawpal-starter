import datetime
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Your daily pet care planner — priority-sorted, time-aware, conflict-free.")

# ---------------------------------------------------------------------------
# Session-state bootstrap
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.subheader("1. Owner info")

with st.form("owner_form"):
    owner_name = st.text_input("Your name", value="Alex")
    available_minutes = st.number_input(
        "Time available today (minutes)", min_value=5, max_value=480, value=90, step=5
    )
    submitted = st.form_submit_button("Save owner info")

if submitted:
    if st.session_state.owner is None:
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes),
        )
    else:
        st.session_state.owner.name = owner_name
        st.session_state.owner.available_minutes = int(available_minutes)
    st.success(f"Saved — {owner_name} has {available_minutes} min today.")

owner: Owner | None = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 2 — Add a pet
# ---------------------------------------------------------------------------
st.divider()
st.subheader("2. Add a pet")

if owner is None:
    st.info("Save owner info above before adding pets.")
else:
    with st.form("pet_form"):
        pet_name = st.text_input("Pet name", value="Luna")
        species   = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
        age       = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
        add_pet_btn = st.form_submit_button("Add pet")

    if add_pet_btn:
        if pet_name in [p.name for p in owner.pets]:
            st.warning(f"A pet named '{pet_name}' already exists.")
        else:
            owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
            st.success(f"Added {species} '{pet_name}' (age {age}).")

    if owner.pets:
        st.write("**Your pets:**")
        for pet in owner.pets:
            st.markdown(f"- **{pet.name}** · {pet.species} · {pet.age} yr")

# ---------------------------------------------------------------------------
# Section 3 — Add tasks
# ---------------------------------------------------------------------------
st.divider()
st.subheader("3. Add a care task")

if owner is None or not owner.pets:
    st.info("Add at least one pet before adding tasks.")
else:
    with st.form("task_form"):
        pet_choices      = [p.name for p in owner.pets]
        selected_pet_name = st.selectbox("Assign to pet", pet_choices)
        task_name        = st.text_input("Task name", value="Morning walk")
        category         = st.selectbox(
            "Category", ["walk", "feed", "meds", "grooming", "enrichment"]
        )

        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
        with col2:
            priority = st.slider("Priority (1 = low, 5 = high)", 1, 5, value=3)

        recurrence_choice = st.selectbox("Recurrence", ["none", "daily"])

        pin_time = st.checkbox("Pin to a specific start time?")
        start_time_minutes: int | None = None
        if pin_time:
            start_time_val     = st.time_input("Start time", value=datetime.time(8, 0))
            start_time_minutes = start_time_val.hour * 60 + start_time_val.minute

        add_task_btn = st.form_submit_button("Add task")

    if add_task_btn:
        target_pet = next(p for p in owner.pets if p.name == selected_pet_name)
        target_pet.add_task(
            Task(
                name=task_name,
                category=category,
                duration_minutes=int(duration),
                priority=priority,
                recurrence=None if recurrence_choice == "none" else recurrence_choice,
                start_time=start_time_minutes,
            )
        )
        st.success(f"Added '{task_name}' to {selected_pet_name}.")

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("**All tasks:**")
        for pet in owner.pets:
            tasks = pet.get_tasks()
            if tasks:
                st.markdown(f"*{pet.name}*")
                rows = [
                    {
                        "Task": t.name,
                        "Category": t.category,
                        "Min": t.duration_minutes,
                        "Priority": "★" * t.priority,
                        "Recurs": t.recurrence or "—",
                        "Pinned": (
                            f"{t.start_time // 60:02d}:{t.start_time % 60:02d}"
                            if t.start_time is not None else "—"
                        ),
                        "Done": "✓" if t.completed else "",
                    }
                    for t in tasks
                ]
                st.table(rows)
    else:
        st.info("No tasks yet. Add one above.")

# ---------------------------------------------------------------------------
# Section 4 — Generate schedule
# ---------------------------------------------------------------------------
st.divider()
st.subheader("4. Generate today's schedule")

if owner is None or not owner.get_all_tasks():
    st.info("Add an owner, at least one pet, and at least one task first.")
else:
    if st.button("Generate schedule", type="primary"):
        scheduler = Scheduler(owner)
        plan      = scheduler.generate_plan()
        conflicts = scheduler._conflicts
        skipped   = scheduler._skipped

        # --- summary metrics ---
        time_used = sum(t.duration_minutes for t in plan)
        col1, col2, col3 = st.columns(3)
        col1.metric("Tasks scheduled", len(plan))
        col2.metric("Time used", f"{time_used} / {owner.available_minutes} min")
        col3.metric("Conflicts", len(conflicts), delta=len(conflicts) or None,
                    delta_color="inverse")

        # --- conflict banners (shown first so owner sees them immediately) ---
        if conflicts:
            st.markdown("#### ⚠ Scheduling conflicts")
            st.caption(
                "These tasks are pinned to overlapping time slots. "
                "Both are kept in the plan — reschedule one to resolve the conflict."
            )
            for warning in conflicts:
                st.warning(warning)

        # --- scheduled tasks ---
        st.markdown("#### Today's plan")
        if not plan:
            st.warning("No tasks fit within today's time budget.")
        else:
            rows = []
            cumulative = 0
            for i, task in enumerate(plan, start=1):
                if task.start_time is not None:
                    slot = f"{task.start_time // 60:02d}:{task.start_time % 60:02d}"
                else:
                    slot = f"~{cumulative // 60:02d}:{cumulative % 60:02d}"
                rows.append({
                    "#": i,
                    "Time": slot,
                    "Task": task.name,
                    "Category": task.category,
                    "Min": task.duration_minutes,
                    "Priority": "★" * task.priority,
                    "Recurs": task.recurrence or "—",
                })
                cumulative += task.duration_minutes
            st.table(rows)

        # --- skipped tasks ---
        if skipped:
            with st.expander(f"Skipped tasks ({len(skipped)}) — not enough time remaining"):
                for t in skipped:
                    st.markdown(
                        f"- **{t.name}** · {t.category} · "
                        f"{t.duration_minutes} min · priority {t.priority}"
                    )

        # --- full explanation ---
        with st.expander("Scheduler reasoning"):
            st.code(scheduler.explain_plan(plan), language=None)
