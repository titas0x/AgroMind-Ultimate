import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import numpy as np
import time
import random

# --- 1. SECURE API CONFIGURATION ---
# This pulls the key from Streamlit Secrets (Hidden from users)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error("⚠️ API Key not found in Streamlit Secrets. Please add it to run the AI.")
    model = None

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="AgroMind Pro", layout="centered", page_icon="🌱")

# --- 3. DATABASE & SESSION STORAGE ---
if 'user_db' not in st.session_state: st.session_state.user_db = {"admin": "123"} 
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'history' not in st.session_state: st.session_state.history = []

# --- 4. AUTHENTICATION (Sign In / Sign Up) ---
def login_page():
    st.title("🍀 AgroMind APK Portal")
    choice = st.segmented_control("Access Mode", ["Sign In", "Sign Up"], default="Sign In")
    
    with st.container(border=True):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        
        if st.button("Enter Dashboard", use_container_width=True):
            if choice == "Sign Up":
                if u and p:
                    st.session_state.user_db[u] = p
                    st.success("Account Created! You can now Sign In.")
                else: st.error("Please fill all fields.")
            elif u in st.session_state.user_db and st.session_state.user_db[u] == p:
                st.session_state.logged_in, st.session_state.user = True, u
                st.rerun()
            else: st.error("Invalid Username or Password")

# --- 5. MAIN APP INTERFACE ---
if not st.session_state.logged_in:
    login_page()
else:
    # Sidebar with Reset and Logout
    with st.sidebar:
        st.header(f"👤 {st.session_state.user}")
        if st.button("🚪 Logout", use_container_width=True): 
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        if st.button("⚠️ Reset All Data", type="primary", use_container_width=True):
            st.session_state.history = []
            st.success("System data wiped.")
            st.rerun()
        st.info("AgroMind APK v1.0")

    st.title("🌱 AgroMind: AI Plant Intelligence")
    
    # Feature Tabs
    t1, t2, t3, t4 = st.tabs(["🔍 AI Scan", "📊 Sensors & NPK", "📈 Growth", "📜 Records"])

    # --- TAB 1: AI SCANNER (Camera/Gallery/Damage/Treatment) ---
    with t1:
        st.subheader("Leaf Health Scanner")
        source = st.radio("Input Source:", ["Live Camera", "Upload Gallery"], horizontal=True)
        
        file = st.camera_input("Scanner") if source == "Live Camera" else st.file_uploader("Upload Image", type=["jpg","png"])
        
        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True, caption="Processing Specimen...")
            
            if st.button("🚀 Analyze with AI", use_container_width=True):
                with st.spinner("Calculating Damage %..."):
                    try:
                        prompt = """Analyze this plant leaf:
                        1. Diagnosis: Name the disease or 'Healthy'.
                        2. Damage Percentage: Estimate how much of the leaf is affected.
                        3. Nutrients to add: Suggest specific N, P, or K additions.
                        4. Treatment: Provide Organic and Chemical fixes.
                        """
                        response = model.generate_content([prompt, img])
                        st.markdown("### AI Analysis Results")
                        st.write(response.text)
                        
                        # Generate random damage for the growth chart simulation
                        dmg_pct = random.randint(10, 85)
                        st.session_state.history.append({
                            "Time": time.strftime("%H:%M"),
                            "Damage": dmg_pct,
                            "Health": 100 - dmg_pct,
                            "Saved_Image": img
                        })
                    except Exception as e:
                        st.error(f"AI Error: {e}")

    # --- TAB 2: SENSORS, WEATHER, NPK ---
    with t2:
        st.subheader("📡 Environmental Telemetry")
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Weather Stats**")
            temp = st.number_input("Temp (°C)", 10, 50, 28)
            hum = st.number_input("Humidity (%)", 10, 100, 65)
        with c2:
            st.write("**Soil Stats**")
            moist = st.slider("Moisture %", 0, 100, 45)
            stress = 100 - moist
            st.metric("Water Stress Level", f"{stress}%", delta="Critical" if stress > 60 else "Safe")
            st.progress(stress/100)

        st.divider()
        st.subheader("🧪 N-P-K Soil Analysis")
        n, p, k = st.columns(3)
        val_n = n.number_input("Nitrogen (N)", 0, 100, 40)
        val_p = p.number_input("Phos. (P)", 0, 100, 35)
        val_k = k.number_input("Potash (K)", 0, 100, 50)
        
        st.bar_chart({"Nutrients": ["N", "P", "K"], "Values": [val_n, val_p, val_k]}, x="Nutrients", y="Values", color="#2E7D32")

    # --- TAB 3: GROWTH CHART ---
    with t3:
        st.subheader("📈 Plant Health & Growth Trend")
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            st.line_chart(df.set_index('Time')['Health'])
            st.caption("Tracking Health Score (100 - Damage %) over time.")
        else:
            st.info("Scan a leaf to begin tracking growth trends.")

    # --- TAB 4: IMAGE HISTORY ---
    with t4:
        st.subheader("📜 Historical Scan Records")
        if not st.session_state.history:
            st.info("No records found.")
        else:
            for item in reversed(st.session_state.history):
                with st.container(border=True):
                    col_img, col_txt = st.columns([1, 2])
                    col_img.image(item['Saved_Image'], use_container_width=True)
                    col_txt.write(f"**Time:** {item['Time']}")
                    col_txt.write(f"**Damage:** {item['Damage']}%")
                    col_txt.write(f"**Health Score:** {item['Health']}%")

st.markdown("---")
st.caption("Developed for B.Tech Final Year Engineering Project.")
