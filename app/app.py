"""Star Type Classifier - Streamlit app.

Run from the repository root:  streamlit run app/app.py
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "star_classifier.joblib"
META_PATH = ROOT / "models" / "model_metadata.json"
DATA_PATH = ROOT / "data" / "stars_clean.csv"

FEATURES = ["Temperature", "L", "R", "A_M"]
LOW_CONFIDENCE = 0.70

# Approximate literature values - verify against SIMBAD / an astronomy reference.
PRESETS = {
    "Custom": None,
    "Sun": (5772.0, 1.0, 1.0, 4.83),
    "Proxima Centauri": (3042.0, 0.0017, 0.154, 15.60),
    "Sirius B": (25200.0, 0.056, 0.0084, 11.18),
    "Rigel": (12100.0, 120000.0, 78.9, -7.84),
    "VY Canis Majoris": (3490.0, 270000.0, 1420.0, -8.0),
}

st.set_page_config(page_title="Star Type Classifier", page_icon="⭐", layout="wide")


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_metadata():
    with open(META_PATH) as f:
        return json.load(f)


@st.cache_data
def load_training_data():
    return pd.read_csv(DATA_PATH)


def load_preset():
    values = PRESETS[st.session_state["preset"]]
    if values is not None:
        (st.session_state["T"], st.session_state["L"],
         st.session_state["R"], st.session_state["M"]) = values


# ---------- state and inputs ----------
for key, default in {"T": 5772.0, "L": 1.0, "R": 1.0, "M": 4.83}.items():
    st.session_state.setdefault(key, default)

st.title("Star Type Classifier")
st.caption("Predict a star's type from its physical properties with a random forest "
           "trained on 240 labelled stars.")

try:
    model = load_model()
    meta = load_metadata()
    train_df = load_training_data()
except FileNotFoundError as err:
    st.error(f"Missing file: {err.filename}. Run the notebooks first to create the model and data files.")
    st.stop()

class_names = {int(k): v for k, v in meta["class_names"].items()}
ranges = meta["training_ranges"]

with st.sidebar:
    st.header("Star properties")
    st.selectbox("Load an example star", list(PRESETS), key="preset", on_change=load_preset)
    st.number_input("Surface temperature (K)", min_value=1.0, step=100.0, format="%g", key="T")
    st.number_input("Luminosity (L / L☉)", min_value=0.0, format="%g", key="L",
                    help="Solar luminosity = 1. Must be greater than 0.")
    st.number_input("Radius (R / R☉)", min_value=0.0, format="%g", key="R",
                    help="Solar radius = 1. Must be greater than 0.")
    st.number_input("Absolute magnitude (Mv)", format="%g", step=0.1, key="M",
                    help="Lower values are brighter. The Sun is about 4.83.")
    st.caption("Example values are approximate; verify before citing.")

T, L, R, M = (st.session_state[k] for k in ("T", "L", "R", "M"))
if min(T, L, R) <= 0:
    st.warning("Temperature, luminosity and radius must all be greater than 0.")
    st.stop()

# ---------- prediction ----------
star = pd.DataFrame([[T, L, R, M]], columns=FEATURES)
proba = model.predict_proba(star)[0]
order = np.argsort(proba)[::-1]
top, second = model.classes_[order[0]], model.classes_[order[1]]
top_p, second_p = proba[order[0]], proba[order[1]]

left, right = st.columns([1, 1.3])
with left:
    st.subheader("Prediction")
    st.metric(class_names[top], f"{top_p:.0%} confidence")
    if top_p < LOW_CONFIDENCE:
        st.warning(f"The model is unsure: {class_names[second]} is also plausible ({second_p:.0%}).")

    outside = [name for name, col in zip(("Temperature", "Luminosity", "Radius", "Magnitude"), FEATURES)
               if not ranges[col][0] <= float(star[col].iloc[0]) <= ranges[col][1]]
    if outside:
        st.warning("Outside the range of the training data: " + ", ".join(outside) +
                   ". Tree-based models cannot extrapolate, so treat this prediction with caution.")

    prob_df = pd.DataFrame({"Type": [class_names[c] for c in model.classes_], "Probability": proba})
    fig_p = px.bar(prob_df.sort_values("Probability"), x="Probability", y="Type", orientation="h",
                   range_x=[0, 1], text=prob_df.sort_values("Probability")["Probability"].map("{:.0%}".format))
    fig_p.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), yaxis_title=None)
    st.plotly_chart(fig_p, width="stretch")

with right:
    st.subheader("Where the star sits on the HR diagram")
    fig = px.scatter(train_df, x="Temperature", y="L", color="Type_Name", log_x=True, log_y=True,
                     category_orders={"Type_Name": [class_names[i] for i in sorted(class_names)]},
                     opacity=0.65, labels={"Temperature": "Temperature (K)", "L": "Luminosity (L/L☉)",
                                           "Type_Name": "Training stars"})
    fig.add_trace(go.Scatter(x=[T], y=[L], mode="markers", name="Your star",
                             marker=dict(symbol="star", size=20, color="gold",
                                         line=dict(width=2, color="black"))))
    fig.update_xaxes(autorange="reversed")      # hot stars on the left, as in a standard HR diagram
    fig.update_layout(height=480, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")

with st.expander("About this model and its limits"):
    st.markdown(
        """
**Model.** Random forest (300 trees) on log10 temperature, log10 luminosity, log10 radius and
absolute magnitude. Cross-validated accuracy on the training data is about 100%.

**Read the accuracy with care.**
- The dataset has only 240 stars, with 40 in each class, which is not a realistic star population.
- The recorded luminosities do not follow the Stefan-Boltzmann law, so the data is not fully
  physically consistent.
- The six classes follow this dataset's definitions. On real, catalogued stars the model got
  8 of 11 right; the misses were cool red supergiants and one red dwarf, where the dataset's
  class boundaries differ from standard astronomical classification.
- Low confidence (below 70%) is a signal that a star lies between classes.

This app is a demonstration of a machine learning workflow, not a scientific classification tool.
        """
    )
