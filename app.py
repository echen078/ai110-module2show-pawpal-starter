import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session-state bootstrap
# Streamlit reruns the entire script on every interaction.  We keep the Owner
# object alive between reruns by storing it in st.session_state, which acts
# as a persistent dictionary for the lifetime of the browser session.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None   # set to an Owner instance once the form is submitted


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
        # First time: create a fresh Owner and migrate any pets that might
        # have been added via a previous (now-reset) owner.
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes),
        )
    else:
        # Update in place so existing pets are preserved.
        st.session_state.owner.name = owner_name
        st.session_state.owner.available_minutes = int(available_minutes)
    st.success(f"Owner saved: {owner_name} ({available_minutes} min available today)")

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
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
        add_pet_btn = st.form_submit_button("Add pet")

    if add_pet_btn:
        existing_names = [p.name for p in owner.pets]
        if pet_name in existing_names:
            st.warning(f"A pet named '{pet_name}' already exists.")
        else:
            owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
            st.success(f"Added {species} '{pet_name}' (age {age}).")

    if owner.pets:
        st.write("**Your pets:**")
        for pet in owner.pets:
            st.markdown(f"- {pet.name} ({pet.species}, {pet.age} yr)")

# ---------------------------------------------------------------------------
# Section 3 — Add tasks
# ---------------------------------------------------------------------------
st.divider()
st.subheader("3. Add a care task")

if owner is None or not owner.pets:
    st.info("Add at least one pet before adding tasks.")
else:
    with st.form("task_form"):
        pet_choices = [p.name for p in owner.pets]
        selected_pet_name = st.selectbox("Assign to pet", pet_choices)

        task_name = st.text_input("Task name", value="Morning walk")
        category = st.selectbox(
            "Category", ["walk", "feed", "meds", "grooming", "enrichment"]
        )
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
        with col2:
            priority = st.slider("Priority (1 = low, 5 = high)", 1, 5, value=3)

        add_task_btn = st.form_submit_button("Add task")

    if add_task_btn:
        target_pet = next(p for p in owner.pets if p.name == selected_pet_name)
        target_pet.add_task(
            Task(
                name=task_name,
                category=category,
                duration_minutes=int(duration),
                priority=priority,
            )
        )
        st.success(f"Added '{task_name}' to {selected_pet_name}.")

    # Show all tasks grouped by pet
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("**All tasks:**")
        for pet in owner.pets:
            if pet.get_tasks():
                st.markdown(f"*{pet.name}*")
                rows = [
                    {
                        "Task": t.name,
                        "Category": t.category,
                        "Duration (min)": t.duration_minutes,
                        "Priority": t.priority,
                        "Done": "✓" if t.completed else "",
                    }
                    for t in pet.get_tasks()
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
        plan = scheduler.generate_plan()
        explanation = scheduler.explain_plan(plan)

        st.markdown("### Today's Plan")
        if not plan:
            st.warning("No tasks fit within today's time budget.")
        else:
            for i, task in enumerate(plan, start=1):
                st.markdown(
                    f"**{i}. {task.name}** — {task.category} · "
                    f"{task.duration_minutes} min · priority {task.priority}"
                )

        st.divider()
        st.markdown("### Scheduler explanation")
        st.code(explanation, language=None)
