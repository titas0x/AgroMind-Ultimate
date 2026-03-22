import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import numpy as np
import time
import io

# --- CONFIG ---
st.set_page_config(page_title="AgroMind Ultimate", layout="wide", page_icon="🍀")

# --- DATABASE & AUTH ---
if 'user_db' not in st.session_state: st.session_state.user_db = {"admin": "123"} 
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'history' not in st.session_state: st.session_state.history = []

def login_system():
    st.title("🔐 AgroMind Portal")
    mode = st.radio("Select:", ["Sign In", "Sign Up"], horizontal=True)
    with st.form("Auth"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Proceed"):
            if mode == "Sign Up":
                st.session_state.user_db[u] = p
                st.success("Account Created! You can now Sign In.")
            elif u in st.session_state.user_db and st.session_state.user_db[u] == p:
                st.session_state.logged_in, st.session_state.user = True, u
                st.rerun()
            else: st.error("Invalid credentials")

if not st.session_state.logged_in:
    login_system()
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title(f"👤 {st.session_state.user}")
        api_key = st.text_input("Enter Gemini API Key", type="password")
        if st.button("🚪 Logout"): 
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        if st.button("🧹 Clear All Data"):
            st.session_state.history = []
            st.success("History Cleared")
        if st.session_state.history:
            # Export CSV (without images)
            df_export = pd.DataFrame(st.session_state.history).drop(columns=['Saved_Image'], errors='ignore')
            st.download_button("📥 Download Report", df_export.to_csv(index=False).encode('utf-8'), "agro_report.csv")

    # --- MAIN TABS ---
    st.title("🍀 AgroMind: AI Agriculture Suite")
    t1, t2, t3, t4 = st.tabs(["🔍 AI Diagnosis", "📊 Sensors", "📚 Care Guide", "📜 History Log"])

    # --- TAB 1: SCAN & GALLERY ---
    with t1:
        if not api_key: st.warning("Please enter API Key in sidebar.")
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # OPTION: Camera or Gallery
            source = st.radio("Image Source:", ["Camera", "Gallery (Upload)"], horizontal=True)
            if source == "Camera":
                file = st.camera_input("Take a picture")
            else:
                file = st.file_uploader("Upload from Gallery", type=["jpg", "png", "jpeg"])

            if file:
                img = Image.open(file)
                st.image(img, width=300, caption="Selected Image")
                if st.button("🚀 Start AI Analysis"):
                    with st.spinner("Analyzing..."):
                        res = model.generate_content(["Diagnose this leaf. Give: 1. Diagnosis, 2. Treatment, 3. Fertility needed.", img])
                        st.subheader("AI Brain Results")
                        st.write(res.text)
                        
                        # SAVE TO HISTORY (Includes the Image)
                        st.session_state.history.append({
                            "Time": time.strftime("%H:%M:%S"),
                            "Diagnosis": "AI Analyzed",
                            "Score": np.random.randint(80, 100),
                            "Saved_Image": img  # Store image object
                        })
                        st.success("Scan saved to History Log!")

    # --- TAB 2: SENSORS & WATER STRESS ---
    with t2:
        st.subheader("📡 Real-time Telemetry")
        c1, c2, c3 = st.columns(3)
        moist = c1.slider("Soil Moisture (%)", 0, 100, 45)
        fert = c2.select_slider("Soil Fertility", ["Poor", "Normal", "Rich"])
        stress = 100 - moist
        c3.metric("Water Stress Level", f"{stress}%")
        st.progress(stress/100)
        st.line_chart(pd.DataFrame(np.random.randn(20, 2), columns=['Moisture', 'Nitrate']))

    # --- TAB 3: TREE IMPROVEMENT ---
    with t3:
        st.subheader("🌳 How to make trees better")
        st.info("**Improvement Strategy:** For Low Moisture, use Drip Irrigation. For Yellow leaves, add Nitrogen.")
        st.write("- **Pruning:** Remove dead leaves to stop disease spread.")
        st.write("- **Mulching:** Add 2 inches of mulch to reduce water stress.")

    # --- TAB 4: HISTORY LOG (With Saved Pictures) ---
    with t4:
        st.subheader("📜 Recent Scans & Images")
        if not st.session_state.history:
            st.info("No scans recorded yet.")
        else:
            for item in reversed(st.session_state.history):
                with st.expander(f"Scan at {item['Time']} - Score: {item['Score']}%"):
                    col_img, col_txt = st.columns([1, 2])
                    if "Saved_Image" in item:
                        col_img.image(item['Saved_Image'], use_container_width=True)
                    col_txt.write(f"**Diagnosis:** {item['Diagnosis']}")
                    col_txt.write("Check Tab 2 for environmental conditions at this time.")
