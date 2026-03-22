import streamlit as st
from PIL import Image
import pandas as pd
import numpy as np
import datetime

# -----------------------------
# Initialize session state safely
# -----------------------------
if 'start_analysis' not in st.session_state:
    st.session_state['start_analysis'] = False
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'leaf_results' not in st.session_state:
    st.session_state['leaf_results'] = []

# -----------------------------
# Leaf Health & Pest Analysis
# -----------------------------
def calculate_health_and_pests(image, dryness_level, texture_score=50):
    img_array = np.array(image)
    r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]

    # Detect unhealthy areas (yellow/brown)
    damage_mask = ((r > 100) & (g < 150) & (b < 100))
    damage_ratio = np.sum(damage_mask)/(img_array.shape[0]*img_array.shape[1])
    color_health = max(0, 100 - damage_ratio*120)

    # Detect visible pests (dark spots)
    pest_mask = ((r < 100) & (g < 100) & (b < 100))
    pest_ratio = np.sum(pest_mask)/(img_array.shape[0]*img_array.shape[1])
    pests_health = max(0, 100 - pest_ratio*150)

    dryness_health = max(0, 100 - dryness_level)
    texture_health = max(0, texture_score)

    health = (color_health*0.35 + dryness_health*0.25 + pests_health*0.25 + texture_health*0.15)
    damage = 100 - health
    confidence = (color_health + dryness_health + pests_health + texture_health)/4

    return round(health,2), round(damage,2), round(confidence,2), damage_mask, pest_mask

def generate_heatmap(image, damage_mask, pest_mask):
    overlay = Image.new('RGBA', image.size, (255,0,0,0))
    overlay_array = np.array(overlay)

    # Red for damaged areas
    overlay_array[damage_mask] = [255,0,0,150]
    # Blue for pest spots
    overlay_array[pest_mask] = [0,0,255,150]

    heatmap = Image.alpha_composite(image.convert('RGBA'), Image.fromarray(overlay_array))
    return heatmap

def treatment_recommendation(health, damage, pest_ratio):
    soil_moisture = max(0, int(50 - (health/2)))
    water_stress = max(0, 50 - soil_moisture)
    treatment = {
        'Watering (ml/day)': max(100, water_stress*20),
        'Nitrogen Fertilizer (g/week)': 10 if damage>20 else 5,
        'Potassium Fertilizer (g/week)': 5 if damage>30 else 2,
        'Pesticide (ml/week)': 5 if pest_ratio>0.01 else 0,
        'Fungicide (ml/week)': 5 if damage>25 else 0
    }
    return treatment

# -----------------------------
# App Tabs
# -----------------------------
tabs = st.tabs(["Leaf Analysis", "Farming Knowledge"])

# -----------------------------
# Leaf Analysis Tab
# -----------------------------
with tabs[0]:
    st.title("🌱 AgroMind: Leaf Health & Pest Analysis System")

    st.markdown("""
    ### Instructions
    1. Click **Start Analysis**.
    2. Capture/upload leaf images.
    3. Input dryness and optional texture score.
    4. View per-leaf heatmap, health, pests, and treatment.
    5. Add to history, track batch, view totals.
    6. Download CSV summary or reset.
    """)

    if st.button("Start Analysis"):
        st.session_state['start_analysis'] = True

    if st.session_state['start_analysis']:
        st.subheader("Input Leaf Image")
        input_option = st.radio("Select Input Method", ["Camera", "Gallery"])
        leaf_images = []

        if input_option == "Camera":
            captured_image = st.camera_input("Capture Leaf Image")
            if captured_image:
                leaf_images.append(captured_image)
        elif input_option == "Gallery":
            uploaded_images = st.file_uploader("Upload Leaf Images", type=['jpg','jpeg','png'], accept_multiple_files=True)
            if uploaded_images:
                leaf_images.extend(uploaded_images)

        if leaf_images:
            global_dryness = st.slider("Default Dryness Level (%)", 0, 100, 10)
            global_texture = st.slider("Leaf Texture Score (0-100)", 0, 100, 50)
            batch_results = []

            for idx, leaf_file in enumerate(leaf_images):
                image = Image.open(leaf_file).convert('RGB')
                st.markdown(f"### Leaf {idx+1}")

                dryness_level = st.slider(f"Leaf {idx+1} Dryness (%)", 0, 100, global_dryness, key=f"dry{idx}")
                texture_score = st.slider(f"Leaf {idx+1} Texture (0-100)", 0, 100, global_texture, key=f"tex{idx}")

                health, damage, confidence, damage_mask, pest_mask = calculate_health_and_pests(image, dryness_level, texture_score)
                pest_ratio = np.sum(pest_mask)/(np.array(image).shape[0]*np.array(image).shape[1])
                treatment = treatment_recommendation(health, damage, pest_ratio)
                heatmap = generate_heatmap(image, damage_mask, pest_mask)

                col1, col2 = st.columns(2)
                with col1:
                    st.image(heatmap, caption=f"Leaf {idx+1} Damage & Pest Heatmap", use_column_width=True)
                    st.write(f"Health: {health}%, Damage: {damage}%, Confidence: {confidence}%, Pest ratio: {round(pest_ratio*100,2)}%")
                with col2:
                    st.write("Dynamic Treatment Suggestions:")
                    treatment_df = pd.DataFrame.from_dict(treatment, orient='index', columns=['Quantity'])
                    st.bar_chart(treatment_df['Quantity'])
                    st.markdown(f"""
                    **Actions for Leaf {idx+1}:**
                    - Water: {treatment['Watering (ml/day)']} ml/day
                    - Nitrogen: {treatment['Nitrogen Fertilizer (g/week)']} g/week
                    - Potassium: {treatment['Potassium Fertilizer (g/week)']} g/week
                    - Pesticide: {treatment['Pesticide (ml/week)']} ml/week if needed
                    - Fungicide: {treatment['Fungicide (ml/week)']} ml/week if needed
                    """)

                batch_results.append({
                    'Leaf': idx+1,
                    'Health %': health,
                    'Damage %': damage,
                    'Confidence %': confidence,
                    'Dryness': dryness_level,
                    'Texture': texture_score,
                    'Pest ratio': round(pest_ratio*100,2),
                    'Treatment': treatment
                })

                if st.button(f"Add Leaf {idx+1} to History"):
                    st.session_state['history'].append({
                        'Leaf': idx+1,
                        'Health %': health,
                        'Damage %': damage,
                        'Pest ratio %': round(pest_ratio*100,2),
                        'Date': datetime.datetime.now()
                    })
                    st.success(f"Leaf {idx+1} added to history!")

            # Batch treatment
            st.subheader("Total Batch Treatment")
            treatment_types = ['Watering (ml/day)','Nitrogen Fertilizer (g/week)','Potassium Fertilizer (g/week)','Pesticide (ml/week)','Fungicide (ml/week)']
            total_treatments = {t:0 for t in treatment_types}
            for r in batch_results:
                for t in treatment_types:
                    total_treatments[t] += r['Treatment'][t]

            total_df = pd.DataFrame(total_treatments.items(), columns=['Treatment','Total Quantity'])
            st.bar_chart(total_df.set_index('Treatment'))

            # CSV download
            st.subheader("Download Batch Summary CSV")
            csv_df = pd.DataFrame([{
                'Leaf': r['Leaf'],
                'Health %': r['Health %'],
                'Damage %': r['Damage %'],
                'Confidence %': r['Confidence %'],
                'Dryness': r['Dryness'],
                'Texture': r['Texture'],
                'Pest ratio %': r['Pest ratio']
            } for r in batch_results])
            csv = csv_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", data=csv, file_name="batch_leaf_summary.csv", mime="text/csv")

            # -----------------------------
            # SAFE Reset Button
            # -----------------------------
            if st.button("Reset Analysis"):
                st.session_state['start_analysis'] = False
                st.session_state['history'] = []
                st.session_state['leaf_results'] = []
                st.experimental_rerun()

# -----------------------------
# Farming Knowledge Tab
# -----------------------------
with tabs[1]:
    st.title("🌾 Farming Knowledge & Harvesting Tips")
    crop = st.selectbox("Select Crop", ["Tomato", "Spinach", "Rice", "Wheat", "Potato"])
    st.subheader(f"{crop} Care Guide & Stages")
    
    guides = {
        "Tomato": {"Growth": "Seedling → Vegetative → Flowering → Fruiting", "Water": "500 ml per plant every 2 days", "Fertilizer": "Nitrogen every 2 weeks, Potassium every 3 weeks", "Pests": "Aphids, Whiteflies", "Harvest": "70–80 days; ripe fruits fully red"},
        "Spinach": {"Growth": "Seedling → Leaf Growth", "Water": "300 ml per plant daily", "Fertilizer": "Balanced NPK once a week", "Pests": "Leaf miners", "Harvest": "30–40 days; harvest outer leaves first"},
        "Rice": {"Growth": "Seedling → Tillering → Panicle Initiation → Maturity", "Water": "Maintain flooded fields early; adjust per stage", "Fertilizer": "Nitrogen every 20 days, Phosphorus at planting", "Pests": "Stem borers", "Harvest": "3–4 months; grains golden-yellow"},
        "Wheat": {"Growth": "Germination → Tillering → Heading → Maturity", "Water": "Moderate; irrigate every 7–10 days", "Fertilizer": "Nitrogen 20 days after sowing", "Pests": "Aphids, Armyworms", "Harvest": "Grains hard; straw golden"},
        "Potato": {"Growth": "Sprouting → Vegetative → Tuber formation → Maturity", "Water": "600 ml per plant every 3 days", "Fertilizer": "Nitrogen early, Potassium mid-growth", "Pests": "Colorado potato beetle", "Harvest": "70–120 days; tubers firm, skin tough"}
    }

    g = guides[crop]
    st.markdown(f"""
**Growth Stages:** {g['Growth']}
**Water Requirement:** {g['Water']}
**Fertilizer Guidance:** {g['Fertilizer']}
**Common Pests:** {g['Pests']}
**Harvesting Tips:** {g['Harvest']}
""")

    st.subheader("Farmer Knowledge Q&A")
    user_question = st.text_input("Ask a farming question (e.g., water, fertilizer, pests, harvest)")
    if user_question:
        responses = {
            "water": f"For {crop}, follow: {g['Water']}",
            "fertilizer": f"For {crop}, follow: {g['Fertilizer']}",
            "pest": f"Common pests for {crop}: {g['Pests']}",
            "harvest": f"Harvesting guide: {g['Harvest']}"
        }
        matched = False
        for key, ans in responses.items():
            if key in user_question.lower():
                st.info(ans)
                matched = True
        if not matched:
            st.warning("No exact match found. Refer to crop guide above for general guidance.")
