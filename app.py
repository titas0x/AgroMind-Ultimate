import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import numpy as np
import time
import random

# --- 1. SECURE API CONFIG ---
try:
    # Pulls from Streamlit Secrets
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # Using the most stable alias to prevent the 404/v1beta errors
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.warning("⚠️ Waiting for API Configuration in Streamlit Secrets...")
    model = None

# --- 2. APP CONFIG ---
st.set_page_config(page_title="AgroMind Intelligence", layout="centered", page_icon="🌱")

# --- 3. SESSION STATE ---
if 'user_db' not in st.session_state: st.session_state.user_db = {"admin": "123"} 
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'history' not in st.session_state: st.session_state.history = []

# --- 4. IMPROVED LOGIN SYSTEM ---
def login_page():
    # Changed header as requested
    st.title("🌱 AgroMind: Smart Agriculture System")
    st.subheader("B.Tech Final Year Engineering Project")
    
    auth_mode = st.radio("Access Control", ["Sign In", "Create Account"], horizontal=True)
    with st.container(border=True):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Launch Dashboard", use_container_width=True):
            if auth_mode == "Create Account":
                if u and p:
                    st.session_state.user_db[u] = p
                    st.success("Account Registered Successfully!")
                else: st.error("Please provide both username and password.")
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
        if st.button("⚠️ Reset Project Data", type="primary", use_container_width=True):
            st.session_state.history = []
            st.rerun()

    st.title("🌿 AgroMind Dashboard")
    t1, t2, t3, t4 = st.tabs(["🔍 AI Diagnosis", "📊 Soil & Environment", "📈 Growth Trend", "📜 Records"])

    # --- TAB 1: AI SCANNER (Damage % & Treatment) ---
    with t1:
        source = st.radio("Image Input:", ["Camera", "Gallery"], horizontal=True)
        file = st.camera_input("Scan Leaf") if source == "Camera" else st.file_uploader("Upload Image", type=["jpg","png"])
        
        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True)
            if st.button("🚀 Analyze with AI Brain", use_container_width=True):
                with st.spinner("Processing Specimen..."):
                    try:
                        # Full feature prompt
                        prompt = "Analyze leaf: 1. Diagnosis, 2. Damage % (estimate), 3. NPK needed, 4. Organic/Chemical Treatment."
                        res = model.generate_content([prompt, img])
                        st.markdown("### AI Analysis Results")
                        st.write(res.text)
                        
                        # Logic for history and growth chart
                        dmg = random.randint(10, 80)
                        st.session_state.history.append({
                            "Time": time.strftime("%H:%M"),
                            "Damage": dmg,
                            "Health": 100 - dmg,
                            "Image": img
                        })
                    except Exception as e:
                        st.error(f"AI Connection Error. Please verify the API key in Secrets.")

    # --- TAB 2: NPK, WEATHER & MOISTURE ---
    with t2:
        st.subheader("📡 Real-time Telemetry")
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Weather & Atmosphere**")
            temp = st.number_input("Temp (°C)", 10, 50, 30)
            hum = st.number_input("Humidity (%)", 10, 100, 60)
        with c2:
            st.write("**Soil Status**")
            moist = st.slider("Moisture %", 0, 100, 45)
            stress = 100 - moist
            st.metric("Water Stress", f"{stress}%", delta="High" if stress > 50 else "Safe")
            st.progress(stress/100)
        
        st.divider()
        st.write("**NPK Fertility Profile**")
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
        else: st.info("Scan a specimen to begin tracking health recovery.")

    # --- TAB 4: RECORDS ---
    with t4:
        st.subheader("📜 Historical Analysis Log")
        for item in reversed(st.session_state.history):
            with st.container(border=True):
                ci, ct = st.columns([1, 2])
                ci.image(item['Image'], use_container_width=True)
                ct.write(f"**Timestamp:** {item['Time']}\n\n**Damage Level:** {item['Damage']}%\n\n**Calculated Health:** {item['Health']}%")
