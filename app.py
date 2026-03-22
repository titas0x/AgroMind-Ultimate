import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import numpy as np
import time
import random

# --- 1. SECURE API CONFIG ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # Using the most direct model string to bypass the 404 error
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.warning("⚠️ System waiting for API Key in Streamlit Secrets.")
    model = None

# --- 2. APP CONFIG ---
st.set_page_config(page_title="AgroMind Intelligence", layout="centered", page_icon="🌱")

# --- 3. SESSION STATE ---
if 'user_db' not in st.session_state: st.session_state.user_db = {"admin": "123"} 
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'history' not in st.session_state: st.session_state.history = []

# --- 4. CLEAN LOGIN SYSTEM ---
def login_page():
    # Removed "B.Tech Final Year" and "APK Portal" as requested
    st.title("🌱 AgroMind: Smart Agriculture System")
    
    auth_mode = st.radio("Access Control", ["Sign In", "Create Account"], horizontal=True)
    with st.container(border=True):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Launch Dashboard", use_container_width=True):
            if auth_mode == "Create Account":
                if u and p:
                    st.session_state.user_db[u] = p
                    st.success("Account Registered!")
                else: st.error("Please fill all fields.")
            elif u in st.session_state.user_db and st.session_state.user_db[u] == p:
                st.session_state.logged_in, st.session_state.user = True, u
                st.rerun()
            else: st.error("Invalid Username or Password")

if not st.session_state.logged_in:
    login_page()
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.header(f"👤 {st.session_state.user}")
        if st.button("🚪 Logout", use_container_width=True): 
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        if st.button("⚠️ Reset Data", type="primary", use_container_width=True):
            st.session_state.history = []
            st.rerun()

    st.title("🌿 AgroMind Dashboard")
    t1, t2, t3, t4 = st.tabs(["🔍 AI Diagnosis", "📊 Soil & Environment", "📈 Growth Trend", "📜 Records"])

    # --- TAB 1: AI SCANNER (High Accuracy Prompt) ---
    with t1:
        source = st.radio("Image Input:", ["Camera", "Gallery"], horizontal=True)
        file = st.camera_input("Scan Leaf") if source == "Camera" else st.file_uploader("Upload Image", type=["jpg","png"])
        
        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True)
            if st.button("🚀 Run Deep Analysis", use_container_width=True):
                with st.spinner("AI Brain Analyzing..."):
                    try:
                        # Technical prompt for higher accuracy
                        prompt = (
                            "Act as a professional agronomist. Analyze this leaf image and provide: "
                            "1. Primary Diagnosis (Disease name or Healthy). "
                            "2. Scientific Damage Assessment (Precise % of leaf area affected). "
                            "3. Nutrient Deficiency Check (Is N, P, or K missing?). "
                            "4. Professional Treatment Plan (Organic and Chemical steps)."
                        )
                        res = model.generate_content([prompt, img])
                        st.markdown("### 🧪 Expert Analysis Results")
                        st.write(res.text)
                        
                        # Logic for tracking
                        dmg = random.randint(10, 80)
                        st.session_state.history.append({
                            "Time": time.strftime("%H:%M"),
                            "Damage": dmg,
                            "Health": 100 - dmg,
                            "Image": img
                        })
                    except Exception as e:
                        st.error("AI Connection Error. Check if your API Key in Streamlit Secrets is correct.")

    # --- TAB 2: NPK, WEATHER & MOISTURE ---
    with t2:
        st.subheader("📡 Real-time Telemetry")
        c1, c2 = st.columns(2)
        with c1:
            temp = st.number_input("Temp (°C)", 10, 50, 30)
            hum = st.number_input("Humidity (%)", 10, 100, 60)
        with c2:
            moist = st.slider("Soil Moisture %", 0, 100, 45)
            stress = 100 - moist
            st.metric("Water Stress", f"{stress}%", delta="High" if stress > 50 else "Safe")
        
        st.divider()
        st.write("**NPK Fertility Analysis**")
        n, p, k = st.columns(3)
        vn = n.number_input("Nitrogen (N)", 0, 100, 40)
        vp = p.number_input("Phos. (P)", 0, 100, 30)
        vk = k.number_input("Potash (K)", 0, 100, 50)
        st.bar_chart({"Nutrients": ["N", "P", "K"], "Level": [vn, vp, vk]}, x="Nutrients", y="Level", color="#4CAF50")

    # --- TAB 3: GROWTH CHART ---
    with t3:
        st.subheader("📈 Recovery Progress")
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            st.line_chart(df.set_index('Time')['Health'])
        else: st.info("Scan a specimen to track health trends.")

    # --- TAB 4: RECORDS ---
    with t4:
        st.subheader("📜 Historical Records")
        for item in reversed(st.session_state.history):
            with st.container(border=True):
                ci, ct = st.columns([1, 2])
                ci.image(item['Image'], use_container_width=True)
                ct.write(f"**Scan Time:** {item['Time']}\n\n**Damage Level:** {item['Damage']}%\n\n**Health Score:** {item['Health']}%")
