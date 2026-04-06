import streamlit as st
from PIL import Image
import numpy as np
import pandas as pd
import datetime
import cv2
import joblib

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

    # AI Prediction
    if model:
        try:
            img_resized = cv2.resize(img_array, (64,64))
            img_flat = img_resized.flatten().reshape(1, -1)
            prediction = model.predict(img_flat)[0]
        except:
            prediction = "Unknown"
    else:
        prediction = "Model not loaded"

    # Color masks
    green = cv2.inRange(hsv, (30,40,40), (90,255,255))
    yellow = cv2.inRange(hsv, (15,50,50), (35,255,255))
    brown = cv2.inRange(hsv, (5,50,50), (20,255,200))

    # Better pest detection
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

    # AI correction
    if prediction == "healthy":
        health = max(85, health)
        pest_ratio = min(0.02, pest_ratio)
        brown_ratio = min(0.02, brown_ratio)
        yellow_ratio = min(0.05, yellow_ratio)
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

    # Primary (AI)
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

    # Secondary (extra issues)
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

    # Healthy case
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

# ----------------- SOIL -----------------
def soil_analysis(h,dryness):
    moisture = max(10,70 - dryness/2 - (100-h)/2)
    water_stress = "High" if moisture<25 else "Moderate" if moisture<50 else "Low"
    fertility = "High" if h>75 else "Moderate" if h>50 else "Low"
    N = max(10,100-h)
    P = max(5,80-h)
    K = max(5,60-h)
    return moisture, water_stress, fertility, N, P, K

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
menu = st.sidebar.radio("Menu",["Analysis","Batch Summary","Water Tracker","Guide","Instructions"])
dryness = st.sidebar.slider("Default Dryness Level",0,100,10)

if st.sidebar.button("Reset All"):
    st.session_state.history=[]
    st.session_state.water_logs=[]
    st.success("All history and water logs cleared!")

# ----------------- ANALYSIS -----------------
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

        moisture,water_stress,fert,N,P,K = soil_analysis(h,dryness)
        st.subheader("🌱 Soil Analysis (Average for Batch)")
        st.write(f"Moisture: {round(moisture,2)}%")
        st.write(f"Water Stress: {water_stress}")
        st.write(f"Fertility: {fert}")

        st.subheader("📊 NPK Levels")
        st.bar_chart(pd.DataFrame({"N":[N],"P":[P],"K":[K]}))

        if st.button("Save to History"):
            st.session_state.history.append({
                "date":datetime.datetime.now(),
                "health":h,"damage":d,"pest":p
            })

        if st.session_state.history:
            df=pd.DataFrame(st.session_state.history)
            st.subheader("Trend Graphs (Average Health & Damage)")
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
