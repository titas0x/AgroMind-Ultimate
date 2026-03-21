import streamlit as st
from PIL import Image, ImageStat
import pandas as pd
import numpy as np
import time
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="AgroMind Ultimate", layout="wide", page_icon="🍀")

# --- 1. SECURE LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 AgroMind Secure Portal")
    with st.form("Login Form"):
        st.subheader("Sign In to Access System")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In")
        
        if submit:
            # Credentials
            if user == "admin" and pw == "agromind2026":
                st.session_state.logged_in = True
                st.success("Access Granted!")
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    st.info("Credentials: admin / agromind2026")

# --- 2. THE MAIN APP ---
if not st.session_state.logged_in:
    login()
else:
    # --- INITIALIZE DATA COLLECTION ---
    if 'history' not in st.session_state:
        st.session_state.history = []

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("👨‍💻 Admin Panel")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()
        
        st.divider()
        if st.button("🧹 Clear All Data"):
            st.session_state.history = []
            st.success("History Cleared.")
        
        # --- DOWNLOAD REPORT FEATURE ---
        if st.session_state.history:
            df_report = pd.DataFrame(st.session_state.history)
            csv = df_report.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Scan Report (CSV)",
                data=csv,
                file_name=f"agromind_report_{time.strftime('%Y%m%d')}.csv",
                mime='text/csv',
            )
        
        st.divider()
        st.subheader("📖 Quick Instructions")
        st.write("1. Use **Camera/Upload** in AI Diagnosis.")
        st.write("2. View **Graphs** in Sensors tab.")
        st.write("3. Export your data via the **Download** button.")

    # --- APP TABS ---
    st.title("🍀 AgroMind Ultimate: Smart Farm Suite")
    tab1, tab2, tab3 = st.tabs(["🔍 AI Diagnosis", "📊 Sensors & Graphs", "📚 Tree Care Guide"])

    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            mode = st.radio("Select Input Source:", ["Camera", "Upload File"])
            img_file = st.camera_input("Scan Leaf") if mode == "Camera" else st.file_uploader("Upload Image", type=["jpg", "png"])

        if img_file:
            img = Image.open(img_file).convert('RGB')
            with col_b:
                st.image(img, caption="Live Input", use_container_width=True)
            
            # --- AI LOGIC (CNN Feature Simulation) ---
            stat = ImageStat.Stat(img)
            r, g, b = stat.mean
            
            # Analysis Logic
            if g > r and g > b:
                diag, conf = "Healthy", 97.2
            elif r > g:
                diag, conf = "Yellow Leaf (Nitrogen Def.)", 86.4
            else:
                diag, conf = "Powdery Mildew", 79.1

            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Diagnosis", diag)
            c2.metric("Confidence", f"{conf}%")
            c3.metric("Database Status", "Saved")
            
            # Save to Session History
            st.session_state.history.append({
                "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "Diagnosis": diag,
                "Confidence": conf
            })

    with tab2:
        st.subheader("📡 Real-time Environmental Telemetry")
        m1, m2, m3 = st.columns(3)
        soil = m1.slider("Soil Moisture (%)", 0, 100, 48)
        hum = m2.slider("Air Humidity (%)", 0, 100, 62)
        stress = m3.progress(soil/100, text="Water Stress Index")
        
        st.divider()
        st.subheader("📈 System Analytics & Data Logs")
        
        # Live Graphs
        chart_data = pd.DataFrame(np.random.randn(20, 2), columns=['Soil Level', 'Humidity'])
        st.line_chart(chart_data)
        
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
        else:
            st.info("No scan history available yet.")

    with tab3:
        st.subheader("🌳 Tree Betterment & Growth Optimization")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **How to improve your trees:**
            - **Soil Aeration:** Use tools to prevent soil compaction around roots.
            - **Nutrient Injections:** If 'Yellow Leaf' is detected, apply Iron Chelates.
            - **Water Management:** Maintain Soil Moisture between 40-60%.
            """)
        with col2:
            st.markdown("""
            **Environmental Stress Controls:**
            - **Humidity Control:** High humidity (>80%) triggers Mildew warnings. 
            - **Water Stress:** If the Stress Index is low, increase drip irrigation frequency.
            """)
