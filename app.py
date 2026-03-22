import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import numpy as np
import time
import random

# --- 1. SECURE API CONFIG (Uses Streamlit Secrets) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.warning("⚠️ System waiting for API Key in Streamlit Secrets.")
    model = None

# --- 2. APP CONFIG ---
st.set_page_config(page_title="AgroMind Ultimate APK", layout="centered", page_icon="🌱")

# --- 3. DATABASE & SESSION STATE ---
if 'user_db' not in st.session_state: st.session_state.user_db = {"admin": "agromind2026"} 
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'history' not in st.session_state: st.session_state.history = []

# --- 4. AUTHENTICATION SYSTEM (Sign In / Sign Up) ---
def login_page():
    st.title("🍀 AgroMind Secure Portal")
    auth_mode = st.radio("Select Action:", ["Sign In", "Create New Account"], horizontal=True)
    
    with st.container(border=True):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        
        if st.button("Proceed to Dashboard", use_container_width=True):
            if auth_mode == "Create New Account":
                if u and p:
                    st.session_state.user_db[u] = p
                    st.success("Account Created! You can now Sign In.")
                else: st.error("Please fill all fields.")
            elif u in st.session_state.user_db and st.session_state.user_db[u] == p:
                st.session_state.logged_in, st.session_state.user = True, u
                st.rerun()
            else: st.error("Invalid Username or Password")

# --- 5. MAIN APPLICATION ---
if not st.session_state.logged_in:
    login_page()
else:
    # Sidebar Controls
    with st.sidebar:
        st.header(f"👤 {st.session_state.user}")
        if st.button("🚪 Logout", use_container_width=True): 
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        if st.button("⚠️ Reset All Data", type="primary", use_container_width=True):
            st.session_state.history = []
            st.success("All records cleared!")
            st.rerun()
        st.info("AgroMind APK v1.0 - B.Tech Project")

    st.title("🌱 AgroMind: AI Plant Intelligence")
    
    # Create Tabs for the 4 Main Sections
    t1, t2, t3, t4 = st.tabs(["🔍 AI Diagnosis", "📊 Sensors & NPK", "📈 Growth Track", "📜 Image History"])

    # --- TAB 1: AI SCANNER (Camera + Gallery + Damage %) ---
    with t1:
        st.subheader("Plant Health Scanner")
        source = st.radio("Select Input:", ["Take Photo (Camera)", "Upload from Gallery"], horizontal=True)
        
        if source == "Take Photo (Camera)":
            file = st.camera_input("Scan Leaf")
        else:
            file = st.file_uploader("Choose Image", type=["jpg", "jpeg", "png"])

        if file:
            img = Image.open(file)
            st.image(img, caption="Processing Specimen...", use_container_width=True)
            
            if st.button("🚀 Analyze with Gemini AI", use_container_width=True):
                if model is None:
                    st.error("AI not configured. Check Secrets.")
                else:
                    with st.spinner("Calculating Damage % and Nutrients..."):
                        try:
                            # Advanced Prompt for specific features
                            prompt = """Analyze this plant leaf:
                            1. Diagnosis: Name the disease or state if healthy.
                            2. Damage Percentage: Estimate the % of leaf area affected.
                            3. Treatment: Provide both Organic and Chemical solutions.
                            4. Nutrients Needed: Which specific N, P, or K additions are required?
                            """
                            response = model.generate_content([prompt, img])
                            st.success("Analysis Complete")
                            st.markdown(response.text)
                            
                            # Log data for history
                            dmg_est = random.randint(5, 95) # Simulation for chart
                            st.session_state.history.append({
                                "Time": time.strftime("%H:%M:%S"),
                                "Damage": dmg_est,
                                "Health": 100 - dmg_est,
                                "Saved_Image": img
                            })
                        except Exception as e:
                            st.error(f"AI Connection Error: {e}")

    # --- TAB 2: SENSORS, NPK & WEATHER ---
    with t2:
        st.subheader("📡 Environmental & Soil Telemetry")
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Weather & Atmosphere**")
            temp = st.number_input("Temp (°C)", 10, 55, 30)
            hum = st.number_input("Humidity (%)", 0, 100, 65)
        with c2:
            st.write("**Soil Status**")
            moist = st.slider("Moisture Level %", 0, 100, 48)
            stress = 100 - moist
            st.metric("Water Stress Level", f"{stress}%", delta="Critical" if stress > 60 else "Healthy")
            st.progress(stress/100)

        st.divider()
        st.subheader("🧪 Soil NPK Analysis")
        n, p, k = st.columns(3)
        val_n = n.number_input("Nitrogen (N)", 0, 100, 40)
        val
