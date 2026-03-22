import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import numpy as np
import time
import re

# --- 1. AI CONFIGURATION (Stable REST Connection) ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        # Fixed: Using 'rest' transport to solve the 404 POST error
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport='rest')
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        model = None
except Exception:
    model = None

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="AgroMind Intelligence", layout="wide", page_icon="🌱")

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'treatment_logs' not in st.session_state: st.session_state.treatment_logs = []

# --- 4. OPEN LOGIN SYSTEM (Any username/password works) ---
def login_page():
    st.title("🌱 AgroMind: Smart Agriculture System")
    st.markdown("---")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Access Dashboard", use_container_width=True):
        if u and p: 
            st.session_state.logged_in = True
            st.session_state.user_name = u
            st.rerun()
        else: 
            st.warning("Please enter credentials to proceed.")

if not st.session_state.logged_in:
    login_page()
else:
    # --- SIDEBAR (Persistent Features) ---
    with st.sidebar:
        st.header(f"👤 {st.session_state.user_name}")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        if st.session_state.history:
            st.subheader("📥 Export Data")
            # Restored Download CSV
            df_csv = pd.DataFrame(st.session_state.history).drop(columns=['SavedImage'])
            st.download_button("Download Full CSV Report", df_csv.to_csv(index=False), "agromind_report.csv")
        if st.button("🗑️ Reset All Data", type="primary", use_container_width=True):
            st.session_state.history = []
            st.session_state.treatment_logs = []
            st.rerun()

    st.title("🌿 AgroMind Command Center")
    tabs = st.tabs(["🔍 AI Diagnosis", "📊 Sensors & NPK", "📝 Treatment Tracker", "📈 Progress Graph", "📜 Summary & Records"])

    # --- TAB 1: HIGH-PRECISION PIXEL ANALYSIS ---
    with tabs[0]:
        src = st.radio("Source:", ["Camera", "Gallery"], horizontal=True)
        file = st.camera_input("Scan Specimen") if src == "Camera" else st.file_uploader("Upload Image", type=["jpg","png"])
        
        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True)
            if st.button("🚀 Run Precise Pixel Analysis", use_container_width=True):
                with st.spinner("Analyzing RGB distribution and structural deformation..."):
                    try:
                        # Integrated Pixel-Focused Prompts
                        prompt = """
                        Detect and classify leaf damage using pixel-level features including:
                        1. Color variation: Chlorosis (yellowing) or Necrosis (black/brown patches).
                        2. Texture irregularities: Fungal spots, lesions, or powdery appearance.
                        3. Structural deformation: Holes, torn edges, curling, or wilting.
                        4. Advanced signals: RGB distribution shifts and edge discontinuities.
                        
                        Provide a specific Damage % and 3 professional treatments.
                        """
                        res = model.generate_content([prompt, img])
                        analysis = res.text
                        nums = re.findall(r'\d+', analysis)
                        dmg = int(nums[0]) if nums else 25
                    except Exception:
                        # Fallback Demo Mode
                        analysis = "⚠️ (Demo Mode) Necrosis and Edge Tearing detected. Damage: 35%. Treatment: Apply Fungicide and improve irrigation."
                        dmg = 35

                    st.success(f"### Diagnosis Result\n{analysis}")
                    st.session_state.history.append({
                        "Date": time.strftime("%Y-%m-%d %H:%M"),
                        "Diagnosis": analysis,
                        "Damage": dmg,
                        "Health": 100 - dmg,
                        "SavedImage": img
                    })

    # --- TAB 2: SENSORS & NPK CHART ---
    with tabs[1]:
        c1, c2 = st.columns(2)
        temp = c1.number_input("Temperature (°C)", 10, 50, 30)
        hum = c1.number_input("Humidity (%)", 10, 100, 60)
        moist = c2.slider("Soil Moisture %", 0, 100, 45)
        c2.metric("Water Stress", f"{100-moist}%", delta="Critical" if moist < 30 else "Safe")
        
        st.divider()
        st.subheader("Soil Fertility (NPK Chart)")
        n, p, k = st.columns(3)
        vn, vp, vk = n.number_input("N"), p.number_input("P"), k.number_input("K")
        # Populating the NPK Chart
        chart_data = pd.DataFrame({"Nutrient": ["N", "P", "K"], "Level": [vn, vp, vk]}).set_index("Nutrient")
        st.bar_chart(chart_data, color="#2E7D32")

    # --- TAB 3: TREATMENT TRACKER ---
    with tabs[2]:
        st.subheader("📝 Activity & Treatment Log")
        col_a, col_b = st.columns(2)
        act = col_a.selectbox("Task:", ["Watering", "Fungicide Spray", "Fertilizer Addition", "Pruning"])
        qty = col_b.text_input("Quantity/Details (e.g. 2 Liters)")
        if st.button("Log Activity"):
            st.session_state.treatment_logs.append({"Time": time.strftime("%H:%M"), "Action": act, "Details": qty})
            st.toast("Treatment Saved!")
        
        if st.session_state.treatment_logs:
            st.table(pd.DataFrame(st.session_state.treatment_logs))

    # --- TAB 4: RECOVERY GRAPH ---
    with tabs[3]:
        st.subheader("📈 Recovery Progress")
        if st.session_state.history:
            df_hist = pd.DataFrame(st.session_state.history)
            st.line_chart(df_hist.set_index('Date')['Health'])
        else: st.info("Graph will populate after scanning specimens.")

    # --- TAB 5: SUMMARY & RECORDS ---
    with tabs[4]:
        if st.session_state.history:
            df_sum = pd.DataFrame(st.session_state.history)
            s1, s2, s3 = st.columns(3)
            s1.metric("Total Scans", len(df_sum))
            # Fixed: Average calculations using numpy
            s2.metric("Avg Health Score", f"{round(np.mean(df_sum['Health']), 1)}%")
            s3.metric("Avg Damage %", f"{round(np.mean(df_sum['Damage']), 1)}%")
            
            st.divider()
            for item in reversed(st.session_state.history):
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    c1.image(item['SavedImage'], use_container_width=True)
                    c2.write(f"**{item['Date']}** | Health: {item['Health']}% | Damage: {item['Damage']}%")
                    c2.caption(item['Diagnosis'])
