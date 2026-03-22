import streamlit as st
from PIL import Image
import numpy as np
import cv2
import pandas as pd
from datetime import datetime
import os
import google.generativeai as genai

# ------------------ CONFIG ------------------
st.set_page_config(page_title="AgroMind AI", layout="wide")

# ------------------ GEMINI SETUP ------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# ------------------ LOGIN ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 AgroMind Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username and password:
            st.session_state.logged_in = True
            st.success("Logged in successfully!")

if not st.session_state.logged_in:
    login()
    st.stop()

# ------------------ FUNCTIONS ------------------

def analyze_leaf(image):
    img = np.array(image)
    img = cv2.resize(img, (224, 224))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_green = np.array([25, 40, 40])
    upper_green = np.array([90, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    green_ratio = np.sum(green_mask > 0) / green_mask.size
    damage = (1 - green_ratio) * 100
    health = green_ratio * 100

    lower_brown = np.array([10, 100, 20])
    upper_brown = np.array([20, 255, 200])
    brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
    brown_ratio = np.sum(brown_mask > 0) / brown_mask.size

    return round(damage,2), round(health,2), round(brown_ratio*100,2)

def estimate_water(damage):
    if damage < 10:
        return 0.2
    elif damage < 30:
        return 0.5
    elif damage < 60:
        return 1.0
    else:
        return 1.5

def estimate_npk(damage, brown_ratio):
    if damage < 15:
        return "10-10-10"
    elif brown_ratio > 20:
        return "10-5-20"
    elif damage > 50:
        return "20-10-10"
    else:
        return "15-15-15"

def water_stress(damage, brown_ratio):
    if brown_ratio > 25:
        return "High"
    elif damage > 40:
        return "Moderate"
    else:
        return "Low"

def soil_insights(damage):
    if damage < 20:
        return "Good", "Healthy"
    elif damage < 50:
        return "Medium", "Moderate"
    else:
        return "Low", "Poor"

def generate_treatment(damage):
    if damage < 10:
        return "No treatment needed. Maintain watering."
    elif damage < 40:
        return "Increase watering slightly and use balanced fertilizer."
    else:
        return "Immediate watering required. Add nitrogen-rich fertilizer and remove damaged leaves."

def save_history(data):
    df = pd.DataFrame([data])
    if os.path.exists("history.csv"):
        old = pd.read_csv("history.csv")
        df = pd.concat([old, df])
    df.to_csv("history.csv", index=False)

# ------------------ UI ------------------

st.title("🌱 AgroMind AI Dashboard")

uploaded_file = st.file_uploader("Upload Leaf Image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Leaf", use_column_width=True)

    damage, health, brown = analyze_leaf(image)
    water = estimate_water(damage)
    npk = estimate_npk(damage, brown)
    stress = water_stress(damage, brown)
    moisture, fertility = soil_insights(damage)
    treatment = generate_treatment(damage)

    st.subheader("📊 Analysis Result")
    col1, col2, col3 = st.columns(3)

    col1.metric("Damage %", f"{damage}%")
    col2.metric("Health %", f"{health}%")
    col3.metric("Water Needed (L/day)", f"{water} L")

    st.subheader("🌿 Insights")
    st.write(f"**Water Stress:** {stress}")
    st.write(f"**Soil Moisture:** {moisture}")
    st.write(f"**Soil Fertility:** {fertility}")
    st.write(f"**Recommended NPK:** {npk}")

    st.subheader("🧾 Treatment")
    st.write(treatment)

    # Gemini Explanation
    prompt = f"""
    A plant has:
    Damage: {damage}%
    Health: {health}%
    Water needed: {water} L/day
    NPK: {npk}

    Explain in simple terms what farmer should do.
    """

    response = model.generate_content(prompt)

    st.subheader("🤖 AI Advice")
    st.write(response.text)

    # Save History
    if st.button("Save to History"):
        save_history({
            "time": datetime.now(),
            "damage": damage,
            "health": health,
            "water": water
        })
        st.success("Saved!")

# ------------------ HISTORY ------------------

st.subheader("📈 Progress Graph")

if os.path.exists("history.csv"):
    df = pd.read_csv("history.csv")
    st.line_chart(df[["damage", "health"]])

    with open("history.csv", "rb") as f:
        st.download_button("📥 Download Data", f, file_name="plant_history.csv")
else:
    st.write("No history yet.")

# ------------------ TRACKER ------------------

st.subheader("🧑‍🌾 Treatment Tracker")

water_input = st.text_input("Water Given (liters)")
fert_input = st.text_input("Fertilizer Used")

if st.button("Save Treatment Log"):
    log = pd.DataFrame([{
        "time": datetime.now(),
        "water": water_input,
        "fertilizer": fert_input
    }])
    if os.path.exists("treatment.csv"):
        old = pd.read_csv("treatment.csv")
        log = pd.concat([old, log])
    log.to_csv("treatment.csv", index=False)
    st.success("Treatment Logged!")
