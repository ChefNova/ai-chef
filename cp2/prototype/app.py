import streamlit as st
from dataclasses import dataclass

st.set_page_config(page_title="ChefNova — CP2 Prototype", page_icon="🍳", layout="wide")

st.title("🍳 ChefNova")
st.caption("Checkpoint 2 prototype — user-confirmed pantry + conversational meal planning")

if "inventory" not in st.session_state:
    st.session_state.inventory = [
        {"item": "Rice", "quantity": 2.0, "unit": "cups", "source": "Receipt", "confirmed": True},
        {"item": "Chickpeas", "quantity": 2.0, "unit": "cans", "source": "Receipt", "confirmed": True},
        {"item": "Spinach", "quantity": 5.0, "unit": "oz", "source": "Receipt", "confirmed": False},
        {"item": "Eggs", "quantity": 6.0, "unit": "count", "source": "Receipt", "confirmed": True},
    ]

if "request" not in st.session_state:
    st.session_state.request = ""

st.info("**Design principle:** AI interprets and recommends; the user owns the truth about what is actually available.")

tab1, tab2, tab3 = st.tabs(["1. Inventory", "2. Meal request", "3. Recommendations"])

with tab1:
    st.subheader("Review your inventory")
    st.write("Receipt-derived items are candidates. Confirmed inventory is the source of truth.")

    edited = []
    for i, row in enumerate(st.session_state.inventory):
        c1, c2, c3, c4, c5 = st.columns([2.2, 1.1, 1.1, 1.3, 1.1])
        item = c1.text_input("Item", row["item"], key=f"item_{i}")
        qty = c2.number_input("Qty", min_value=0.0, value=float(row["quantity"]), step=0.5, key=f"qty_{i}")
        unit = c3.text_input("Unit", row["unit"], key=f"unit_{i}")
        source = c4.text_input("Source", row["source"], key=f"source_{i}")
        confirmed = c5.checkbox("Confirmed", value=row["confirmed"], key=f"confirmed_{i}")
        edited.append({"item": item, "quantity": qty, "unit": unit, "source": source, "confirmed": confirmed})

    if st.button("Save inventory", type="primary"):
        st.session_state.inventory = edited
        st.success("Inventory saved. Only confirmed items will be treated as available.")

    st.caption("Uncertain receipt quantities should be confirmed by the user rather than silently inferred.")

with tab2:
    st.subheader("Tell ChefNova what you want")
    st.session_state.request = st.text_area(
        "Meal request",
        value=st.session_state.request,
        placeholder="e.g., I want a vegetarian, high-protein dinner under 20 minutes.",
        height=120,
    )

    if st.button("Interpret request"):
        text = st.session_state.request.lower()
        constraints = []
        if "vegetarian" in text:
            constraints.append("Vegetarian")
        if "vegan" in text:
            constraints.append("Vegan")
        if "protein" in text:
            constraints.append("High protein")
        if "20" in text and "minute" in text:
            constraints.append("≤ 20 minutes")
        if "dairy" in text and ("no dairy" in text or "avoid dairy" in text):
            constraints.append("No dairy")
        if "mushroom" in text and ("no mushroom" in text or "avoid mushroom" in text):
            constraints.append("No mushrooms")
        st.session_state.constraints = constraints
        st.success("Request interpreted. Review the constraints before relying on a recommendation.")

    if "constraints" in st.session_state:
        st.write("**Active constraints:**")
        for c in st.session_state.constraints:
            st.write(f"- {c}")

with tab3:
    st.subheader("Recommendations")
    confirmed = [x for x in st.session_state.inventory if x["confirmed"] and x["quantity"] > 0]
    names = {x["item"].lower() for x in confirmed}

    if not confirmed:
        st.warning("Confirm at least one inventory item first.")
    else:
        st.write("**Confirmed available:** " + ", ".join(x["item"] for x in confirmed))

        has_oven = st.checkbox("I have an oven", value=False)
        candidates = [
            {
                "name": "Chickpea Spinach Rice Bowl",
                "required": ["chickpeas", "rice"],
                "optional": ["spinach"],
                "time": 15,
                "diet": "vegetarian",
                "equipment": "pan",
                "reason": "Uses confirmed chickpeas and rice. Spinach is optional in this demo. Protein figure is a demo estimate, not a measured value."
            },
            {
                "name": "Egg & Spinach Rice Bowl",
                "required": ["eggs", "rice"],
                "optional": ["spinach"],
                "time": 12,
                "diet": "vegetarian",
                "equipment": "pan",
                "reason": "Uses confirmed eggs and rice. Spinach can be omitted if unavailable."
            },
            {
                "name": "Oven Tomato Chickpea Bake",
                "required": ["chickpeas"],
                "optional": [],
                "time": 25,
                "diet": "vegetarian",
                "equipment": "oven",
                "reason": "Needs an oven even when the ingredients are in the pantry."
            },
        ]

        constraints = [c.lower() for c in st.session_state.get("constraints", [])]
        ranked = []
        for recipe in candidates:
            missing = [x for x in recipe["required"] if x not in names]
            vegetarian_ok = "vegetarian" not in constraints or recipe["diet"] == "vegetarian"
            time_ok = "≤ 20 minutes" not in constraints or recipe["time"] <= 20
            equipment_ok = recipe["equipment"] != "oven" or has_oven
            if missing or not vegetarian_ok or not time_ok or not equipment_ok:
                rank = 0
            else:
                rank = 1
            ranked.append((rank, recipe, missing, vegetarian_ok, time_ok, equipment_ok))
        ranked.sort(key=lambda row: row[0], reverse=True)

        for _, recipe, missing, vegetarian_ok, time_ok, equipment_ok in ranked:
            st.markdown(f"### {recipe['name']}")
            if not equipment_ok:
                st.error("Not feasible with the saved kitchen — this recipe needs an oven.")
            elif missing:
                st.error("Not directly feasible — missing required: " + ", ".join(missing))
                st.caption("A missing optional item can still be Cook Now. A missing core item cannot. Any suggested swap is possible, not a guaranteed safe substitution.")
            elif not vegetarian_ok:
                st.error("Filtered — a hard dietary constraint is not a ranking tie-break.")
            elif not time_ok:
                st.error("Filtered — exceeds the active time constraint.")
            else:
                st.success(f"Cook now · ~{recipe['time']} minutes")
                st.write(recipe["reason"])

        st.divider()
        st.caption("Cook Now recipes are listed first. Diet and time are hard filters. The fuller design prototype is ChefNova_app_UI.py at the repo root.")
