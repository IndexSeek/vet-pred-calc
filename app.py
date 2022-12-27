import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, ColumnsAutoSizeMode
from st_aggrid.grid_options_builder import GridOptionsBuilder

st.title("Veterinary Prednisone/Prednisolone Dose Calculator")
st.write(
    "This application calculates the dose of prednisone or prednisolone in mg/kg for dogs or cats."
)
SHOW_WORK = st.checkbox("Would you like for us to show our work?")

st.write("Please select the species.")
species = st.selectbox("Species", ("Dog 🐕", "Cat 🐈"))
selected_species = species.split(" ")[0].lower()

st.write("Please enter the patient's weight.")
weight_col, unit_col = st.columns(2)
with weight_col:
    weight = st.number_input("Weight", min_value=0, max_value=100, value=0, step=1)
with unit_col:
    unit = st.selectbox("Unit", ("lb", "kg"))

weight_kg = weight / 2.2 if unit == "lb" else weight

if SHOW_WORK:
    if unit == "lb":
        st.write(
            f"Your {selected_species} weighs {weight} {unit}s. ({round(weight_kg, 2)} kgs)"
        )
    elif unit == "kg":
        st.write(
            f"Your {selected_species} weighs {weight_kg} {unit}s. ({round(weight * 2.2, 2)} lbs)"
        )

st.write("Please select the condition.")
condition = st.selectbox(
    "Condition",
    (
        "Physiological Replacement",
        "Anti-inflammatory",
        "Anti-Neoplastic",
        "Immunosuppressive",
    ),
)

condition_multiplier = {
    "Physiological Replacement": [0.25, 0.25, 0.25],
    "Anti-inflammatory": [0.5, 0.625, 0.75],
    "Anti-Neoplastic": [1, 1, 1],
    "Immunosuppressive": [2, 3, 4],
}

severity_levels = ["Mild", "Moderate", "Severe"]

severity_selector = {
    "Mild": 0,
    "Moderate": 1,
    "Severe": 2,
}

if condition in ["Anti-inflammatory", "Immunosuppressive"]:
    selected_severity = st.select_slider("Severity", severity_levels, value="Mild")
else:
    selected_severity = "Mild"

med_dosage = condition_multiplier[condition][severity_selector[selected_severity]]

if SHOW_WORK:
    st.write(
        f"We're multiplying {round(weight_kg, 2)} ({selected_species}'s weight in kg) by {med_dosage} mg/kg (dosage for {condition.lower()})."
    )
    if condition in ["Anti-inflammatory", "Immunosuppressive"]:
        st.write(
            f"Since you've selected {condition} as the condition for the {selected_species} we need to factor in severity. With a {selected_severity.lower()} severity level we need to multiply by {med_dosage} mg/kg."
        )
    else:
        st.write(
            f"Since you've selected {condition} as the condition for the {selected_species} we don't need to factor in severity."
        )
    st.write("")

calculated_dose = weight_kg * med_dosage

st.write(f"Dose: {round(calculated_dose, 2)} mg")


medication_options = pd.read_csv("medication-options.csv")


def instruction_text(row):
    form = (
        row["Form"].lower() + "s"
        if row["Form"] == "Tablet" and row["RoundedCalculatedDosage"] > 1
        else row["Form"].lower()
    )
    if row["Form"] == "Liquid":
        return f"""Give {row['RoundedCalculatedDosage']} mL by mouth every 12 hours for 7 days. (TWICE DAILY)
Then give {row['RoundedCalculatedDosage']} mL by mouth every 24 hours for 7 days. (ONCE DAILY)
Then give {row['RoundedCalculatedDosage']} mL by mouth every 48 hours for 7 days. (EVERY OTHER DAY)"""
    elif row["Form"] == "Tablet" and row["Type"] == "Half":
        return f"""Give {int(row['RoundedCalculatedDosage'])} half {form} by mouth every 12 hours for 7 days. (TWICE DAILY)
Then give {int(row['RoundedCalculatedDosage'])} half {form} by mouth every 24 hours for 7 days. (ONCE DAILY)
Then give {int(row['RoundedCalculatedDosage'])} half {form} by mouth every 48 hours for 7 days. (EVERY OTHER DAY)"""
    elif row["Form"] == "Tablet" and row["Type"] == "Whole":
        return f"""Give {int(row['RoundedCalculatedDosage'])} {form} by mouth every 12 hours for 7 days. (TWICE DAILY)
Then give {int(row['RoundedCalculatedDosage'])} {form} by mouth every 24 hours for 7 days. (ONCE DAILY)
Then give {int(row['RoundedCalculatedDosage'])} {form} by mouth every 48 hours for 7 days. (EVERY OTHER DAY)"""


medication_options["CalculatedDosage"] = round(
    calculated_dose / medication_options["Milligrams"], 2
)
medication_options["RoundedCalculatedDosage"] = medication_options.apply(
    lambda x: round(x["CalculatedDosage"], 1)
    if x["Form"] == "Liquid"
    else round(x["CalculatedDosage"]),
    axis=1,
)
medication_options["InstructionText"] = medication_options.apply(
    instruction_text, axis=1
)
medication_options["TotalAmount"] = medication_options.apply(
    lambda x: round(x["RoundedCalculatedDosage"] * 25, 1)
    if x["Type"] == "Whole"
    else round(x["RoundedCalculatedDosage"] * 25 / 2, 1),
    axis=1,
)


def abbreviate_medication(row):
    if row["Type"] == "Half":
        return f"{round(row['Milligrams'] * 2)} mg {row['Medication']} {row['Type']}"
    elif row["Type"] == "Whole" and row["Form"] == "Tablet":
        return f"{round(row['Milligrams'])} mg {row['Medication']} {row['Type']}"
    elif row["Type"] == "Whole" and row["Form"] == "Liquid":
        return f"{round(row['Milligrams'])} mg/mL {row['Medication']} {row['Form']}"


medication_options["Medication Description"] = medication_options.apply(
    abbreviate_medication, axis=1
)

if weight_kg > 0:
    gb = GridOptionsBuilder.from_dataframe(
        medication_options[["Medication Description", "CalculatedDosage"]]
    )
    gb.configure_selection(selection_mode="single", use_checkbox=True)
    gb.configure_column("Medication Description", sortable=False, width=300)
    gb.configure_column("CalculatedDosage", sortable=False, width=100)
    gridOptions = gb.build()
    response = AgGrid(
        medication_options,
        gridOptions=gridOptions,
        enable_enterprise_modules=False,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        fit_columns_on_grid_load=True,
    )

    if response.selected_rows:
        index = response.selected_rows[0]["_selectedRowNodeInfo"]["nodeRowIndex"]
        print(index)

        instruction_text = medication_options.iloc[index]["InstructionText"]
        total_amount = medication_options.iloc[index]["TotalAmount"]

        st.write(instruction_text)

        if medication_options.iloc[index]["Form"] == "Tablet":
            st.write(f"{round(total_amount, 1)} total tablets.")
        elif medication_options.iloc[index]["Form"] == "Liquid":
            st.write(f"{round(total_amount, 1)} total mL.")
