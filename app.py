import streamlit as st
from PIL import Image
import numpy as np
import pandas as pd
import datetime
import cv2
import joblib
import requests

st.set_page_config(page_title="AgroMind", layout="wide")

# ----------------- LOAD MODEL -----------------
try:
    model = joblib.load("leaf_model.pkl")
except:
    model = None

# ----------------- SESSION STATE -----------------
if "history" not in st.session_state:
    st.session_state.history = []
if "water_logs" not in st.session_state:
    st.session_state.water_logs = []

# ----------------- BACKEND -----------------
API_URL = "https://agromind-server.onrender.com/data"

def get_sensor_data():
    try:
        res = requests.get(API_URL, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                return data[-1]
            elif isinstance(data, dict) and len(data) > 0:
                return data
        return None
    except:
        return None

sensor_data = get_sensor_data()

ph = None
moisture_sensor = None
pump_status = "OFF"

# ----------------- DHT22 ADDED (NEW) -----------------
temperature = None
humidity_air = None

if sensor_data:
    ph = sensor_data.get("ph")
    moisture_sensor = sensor_data.get("soil_moisture")

    pump = sensor_data.get("pump", 0)

    if pump == 1:
        pump_status = "ON"
    else:
        pump_status = "OFF"

    # ----------------- DHT22 DATA (NEW ADDITION) -----------------
    temperature = sensor_data.get("temperature")
    humidity_air = sensor_data.get("humidity")

# ----------------- PH BASED FERTILITY -----------------
def get_fertility_from_ph(ph):
    if ph is None:
        return None
    if ph < 5.5:
        return "Low"
    elif ph <= 7.5:
        return "Moderate"
    else:
        return "High"

# ----------------- WATER STRESS -----------------
def get_water_stress(m):
    if m is None:
        return None
    if m < 25:
        return "High"
    elif m < 50:
        return "Moderate"
    else:
        return "Low"

# ----------------- PREPROCESS -----------------
def preprocess(img):
    img = img.resize((256,256))
    img_array = np.array(img)
    blur = cv2.GaussianBlur(img_array,(5,5),0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    return img_array, hsv, gray

# ----------------- ANALYZE -----------------
def analyze_leaf(img, dryness):
    img_array, hsv, gray = preprocess(img)

    if model:
        try:
            img_resized = cv2.resize(img_array, (64,64))
            img_flat = img_resized.flatten().reshape(1, -1)
            prediction = model.predict(img_flat)[0]
        except:
            prediction = "Unknown"
    else:
        prediction = "Model not loaded"

    green = cv2.inRange(hsv, (30,40,40), (90,255,255))
    yellow = cv2.inRange(hsv, (15,50,50), (35,255,255))
    brown = cv2.inRange(hsv, (5,50,50), (20,255,200))

    edges = cv2.Canny(gray, 50, 150)
    pest_mask = edges

    total = 256*256
    green_ratio = np.sum(green>0)/total
    yellow_ratio = np.sum(yellow>0)/total
    brown_ratio = np.sum(brown>0)/total
    pest_ratio = np.sum(pest_mask>0)/total

    health = green_ratio*100 - brown_ratio*150 - pest_ratio*120 - yellow_ratio*80 - dryness*0.15
    health = max(5,min(100,health))
    damage = 100-health

    if prediction == "healthy":
        health = max(85, health)
        damage = 100-health

    return {
        "health": health,
        "damage": damage,
        "pest_ratio": pest_ratio,
        "green_mask": green,
        "yellow_mask": yellow,
        "brown_mask": brown,
        "pest_mask": pest_mask,
        "yellow_ratio": yellow_ratio,
        "brown_ratio": brown_ratio,
        "ai_prediction": prediction
    }

# ----------------- MULTI-DISEASE DETECTION -----------------
def detect_disease(res, dryness):

    diseases = []
    solutions = []
    meds = []

    pred = res.get("ai_prediction")

    if pred == "fungal":
        diseases.append("Fungal Infection")
        solutions.append("Apply antifungal spray")
        meds.append(["Carbendazim","Mancozeb"])

    elif pred == "pest":
        diseases.append("Pest Attack")
        solutions.append("Use insecticide or neem oil")
        meds.append(["Neem Oil","Imidacloprid"])

    elif pred == "nutrient":
        diseases.append("Nutrient Deficiency")
        solutions.append("Add fertilizers")
        meds.append(["NPK","Vermicompost"])

    if res["brown_ratio"] > 0.15:
        if "Fungal Infection" not in diseases:
            diseases.append("Fungal Infection")
            solutions.append("Apply antifungal spray")
            meds.append(["Carbendazim"])

    if res["pest_ratio"] > 0.05:
        if "Pest Attack" not in diseases:
            diseases.append("Pest Attack")
            solutions.append("Use neem oil")
            meds.append(["Neem Oil"])

    if res["yellow_ratio"] > 0.25:
        if "Nutrient Deficiency" not in diseases:
            diseases.append("Nutrient Deficiency")
            solutions.append("Add fertilizers")
            meds.append(["NPK"])

    if dryness > 60:
        diseases.append("Water Stress")
        solutions.append("Increase watering")
        meds.append(["Irrigation"])

    if not diseases:
        diseases = ["Healthy Leaf"]
        solutions = ["No action needed"]
        meds = [["None"]]

    return diseases, solutions, meds

# ----------------- MULTI VIEW -----------------
def multi_view(images, dryness):
    results=[]
    combined_y = combined_b = combined_p = None
    H,D,P,YR,BR = [],[],[],[],[]
    for img in images:
        res = analyze_leaf(img, dryness)
        results.append(res)
        H.append(res["health"])
        D.append(res["damage"])
        P.append(res["pest_ratio"])
        YR.append(res["yellow_ratio"])
        BR.append(res["brown_ratio"])
        if combined_y is None:
            combined_y = res["yellow_mask"]
            combined_b = res["brown_mask"]
            combined_p = res["pest_mask"]
        else:
            combined_y |= res["yellow_mask"]
            combined_b |= res["brown_mask"]
            combined_p |= res["pest_mask"]
    return results, np.mean(H), np.mean(D), np.mean(P), combined_y, combined_b, combined_p, np.mean(YR), np.mean(BR)

# ----------------- HEATMAP -----------------
def heatmap(img,y,b,p):
    base = img.resize((256,256)).convert("RGBA")
    overlay = np.zeros((256,256,4),dtype=np.uint8)
    overlay[y>0] = [255,255,0,120]
    overlay[b>0] = [255,0,0,150]
    overlay[p>0] = [0,0,255,120]
    return Image.alpha_composite(base, Image.fromarray(overlay))

# ----------------- GUIDE -----------------
crops_general = ["Rice","Wheat","Maize","Potato","Tomato","Onion","Sugarcane","Carrot","Spinach","Soybean"]

def answer_query(q):
    q=q.lower()
    if "water" in q: return "Water early morning or evening"
    if "fertilizer" in q: return "Use balanced NPK fertilizer"
    if "pest" in q: return "Use neem oil or organic pesticide"
    return "Maintain soil health and monitor regularly"

# ----------------- INSTRUCTIONS -----------------
def farming_instructions():
    return [
        "🌱 Water plants early morning or late evening to reduce evaporation.",
        "🧪 Use balanced fertilizers based on soil condition.",
        "🐛 Monitor leaves for yellowing, browning, or pest activity.",
        "🌞 Ensure adequate sunlight and spacing.",
        "🧹 Remove severely damaged leaves to prevent disease spread.",
        "💧 Mulching retains soil moisture in dry conditions.",
        "🩺 Apply treatment based on condition carefully."
    ]

# ----------------- UI -----------------
st.title("🌱 AgroMind System")

# -------- SENSOR DASHBOARD --------
st.subheader("📡 Live Sensor Data")

if sensor_data:

    col1, col2, col3 = st.columns(3)

    col1.metric("🌡️ Soil pH", ph if ph is not None else "N/A")
    col2.metric("💧 Soil Moisture (%)", moisture_sensor if moisture_sensor is not None else "N/A")
    col3.metric("🚿 Water Pump", pump_status)

    # ----------------- DHT22 UI (NEW ADDITION) -----------------
    st.metric("🌡️ Temperature (°C)", temperature if temperature is not None else "N/A")

    fertility = get_fertility_from_ph(ph)
    water_stress = get_water_stress(moisture_sensor)

    st.subheader("🌱 Soil Analysis (Sensor-Based)")
    st.write(f"Moisture: {moisture_sensor}%")
    st.write(f"Water Stress: {water_stress}")
    st.write(f"Fertility (from pH): {fertility}")

else:
    st.error("❌ No data received")

# -------- MENU --------
menu = st.sidebar.radio("Menu",["Analysis","Batch Summary","Water Tracker","Guide","Instructions"])
dryness = st.sidebar.slider("Default Dryness Level",0,100,10)

if st.sidebar.button("Reset All"):
    st.session_state.history=[]
    st.session_state.water_logs=[]
    st.success("All history and water logs cleared!")

# -------- ANALYSIS --------
if menu=="Analysis":
    mode = st.radio("Input Mode",["Camera","Upload"])
    leaf_images=[]

    if mode=="Camera":
        cam = st.camera_input("Capture Leaf")
        if cam:
            leaf_images.append(Image.open(cam))
    else:
        files = st.file_uploader("Upload Multiple Images",accept_multiple_files=True)
        if files:
            leaf_images=[Image.open(f) for f in files]

    if leaf_images:
        results, h,d,p,y,b,pe,yr,br = multi_view(leaf_images,dryness)
        st.subheader("🌿 Individual Leaf Analysis")

        for idx,res in enumerate(results):
            diseases, solutions, meds = detect_disease(res, dryness)

            st.write(f"**Leaf {idx+1}:**")
            st.write(f"Health: {round(res['health'],2)}%, Damage: {round(res['damage'],2)}%, Pest Ratio: {round(res['pest_ratio']*100,2)}%")

            st.info(f"🌿 AI Diagnosis: {res['ai_prediction']}")

            st.image(leaf_images[idx])
            st.image(heatmap(leaf_images[idx],res["yellow_mask"],res["brown_mask"],res["pest_mask"]))

            for i, disease in enumerate(diseases):
                st.warning(disease)
                st.write("Treatment Priority:", solutions[i])
                st.write("Medicine Recommendations:", ", ".join(meds[i]))

            st.markdown("---")

        st.subheader("📊 NPK Levels")
        st.bar_chart(pd.DataFrame({"N":[50],"P":[40],"K":[30]}))

        if st.button("Save to History"):
            st.session_state.history.append({
                "date":datetime.datetime.now(),
                "health":h,"damage":d,"pest":p
            })

        if st.session_state.history:
            df=pd.DataFrame(st.session_state.history)
            st.subheader("Trend Graphs")
            st.line_chart(df[["health","damage"]])
            st.download_button("Download CSV",df.to_csv(index=False),"agromind_data.csv")

elif menu=="Batch Summary":
    st.dataframe(pd.DataFrame(st.session_state.history))

elif menu=="Water Tracker":
    water = st.number_input("Water Given (ml)")
    treatment = st.text_input("Treatment Applied")
    if st.button("Save Log"):
        st.session_state.water_logs.append({
            "date":datetime.datetime.now(),
            "water":water,"treatment":treatment
        })
    st.subheader("Water Logs")
    st.write(st.session_state.water_logs)

elif menu=="Guide":
    st.subheader("🌾 Crop Guide")
    for c in crops_general:
        st.write(f"**{c}**: Maintain soil, monitor pests and nutrients regularly")
    st.subheader("❓ Ask Farming Question")
    q = st.text_input("Type your question")
    if q:
        st.success(answer_query(q))

elif menu=="Instructions":
    st.subheader("📖 Farming Instructions & Tips")
    for tip in farming_instructions():
        st.write(tip)