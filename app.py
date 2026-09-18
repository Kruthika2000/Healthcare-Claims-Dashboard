import streamlit as st
import pandas as pd
import sqlite3
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# --- 1. DATA GENERATION ENGINE (ENHANCED US HEALTHCARE SCHEMAS) ---
def init_db():
    conn = sqlite3.connect('healthcare_analytics.db')
    cursor = conn.cursor()
    
    # Reset table to apply new structural columns cleanly
    cursor.execute("DROP TABLE IF EXISTS claims")
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS claims (
        claim_id TEXT PRIMARY KEY,
        patient_id TEXT,
        patient_age INTEGER,
        patient_gender TEXT,
        provider_name TEXT,
        npi_number TEXT,
        icd10_code TEXT,
        cpt_code TEXT,
        pos_code TEXT,
        billed_amount REAL,
        deductible_applied REAL,
        coinsurance_applied REAL,
        copay_applied REAL,
        allowed_amount REAL,
        status TEXT,
        submission_date TEXT,
        rejection_reason TEXT
    )''')
    
    providers = {
        "Seoul General Hospital": "1982730491", 
        "Asan Medical Center": "1457392014", 
        "Samsung Medical": "1029384756", 
        "Yonsei Severance": "1847392019"
    }
    
    # US Healthcare standard data mappings
    icd10_map = {"I10": "Hypertension", "E11.9": "Type 2 Diabetes", "J45.909": "Asthma", "Z00.00": "General Checkup"}
    cpt_map = {"99213": "Outpatient Visit (15 min)", "99214": "Outpatient Visit (25 min)", "93000": "EKG tracing", "36415": "Blood draw"}
    pos_map = {"11": "Office", "21": "Inpatient Hospital", "22": "On-Campus Outpatient"}
    genders = ["M", "F", "U"]

    for i in range(1, 300):
        c_id = f"CLM-{2000 + i}"
        p_id = f"PT-{random.randint(5000, 9999)}"
        age = random.randint(18, 85)
        gender = random.choice(genders)
        prov = random.choice(list(providers.keys()))
        npi = providers[prov]
        icd = random.choice(list(icd10_map.keys()))
        cpt = random.choice(list(cpt_map.keys()))
        pos = random.choice(list(pos_map.keys()))
        billed = round(random.uniform(80.0, 6200.0), 2)
        date = (datetime.now() - timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d')
        
        # Financial defaults
        deductible = 0.0
        coinsurance = 0.0
        copay = 0.0
        reason = "Approved per Standard Schedule Fee"
        
        # --- ENHANCED ADJUDICATION COMPLEX RULES ENGINE ---
        if billed > 5000.0 and pos == "11":
            status, allowed, reason = "Denied", 0.0, "POS Error: Office billed amount exceeds structural threshold limits."
        elif age > 65 and icd == "Z00.00" and billed > 3000.0:
            status, allowed, reason = "Pending Review", round(billed * 0.5, 2), "Senior Preventive Audit: High dollar routine checkup validation required."
        elif cpt == "93000" and icd == "E11.9" and random.random() < 0.30:
            status, allowed, reason = "Denied", 0.0, "Medical Necessity Denial: EKG diagnostic code mismatch for basic diabetes check."
        elif random.random() < 0.08:
            status, allowed, reason = "Denied", 0.0, "Duplicate Transaction Profile detected within a 72-hour window."
        else:
            status = "Approved"
            allowed = round(billed * 0.82, 2)
            # Break down financial components
            copay = 25.00 if pos == "11" else 100.00
            if allowed > copay:
                coinsurance = round((allowed - copay) * 0.20, 2)
            else:
                copay = allowed
                
        cursor.execute("INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                       (c_id, p_id, age, gender, prov, npi, icd, cpt, pos, billed, deductible, coinsurance, copay, allowed, status, date, reason))
        
    conn.commit()
    conn.close()

init_db()

# --- 2. DATA EXTRACTION LAYER ---
conn = sqlite3.connect('healthcare_analytics.db')
df = pd.read_sql_query("SELECT * FROM claims", conn)
conn.close()

# --- 3. STREAMLIT ENTERPRISE UI DASHBOARD ---
st.set_page_config(page_title="US Healthcare Claims Engine Dashboard", layout="wide")

st.title("🏥 Core US Healthcare Claims Adjudication & Analytics Suite")
st.markdown("Automated Clearinghouse Rule Engine Proof-of-Concept | Developed by Tech PM / Data Analyst Candidates")

# --- INTERACTIVE DASHBOARD SIDEBAR FILTERS ---
st.sidebar.header("⚙️ Core Adjudication Filters")
selected_prov = st.sidebar.multiselect("Provider Network Filter:", options=df["provider_name"].unique(), default=df["provider_name"].unique())
selected_status = st.sidebar.multiselect("Adjudication State Filter:", options=df["status"].unique(), default=df["status"].unique())
selected_pos = st.sidebar.multiselect("Place of Service (POS) Filter:", options=df["pos_code"].unique(), default=df["pos_code"].unique())

# Dynamically apply the multiple layers of UI filters
f_df = df[(df["provider_name"].isin(selected_prov)) & (df["status"].isin(selected_status)) & (df["pos_code"].isin(selected_pos))]

# --- METRIC HEADERS ---
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("Total Claims Processed", f"{len(f_df):,}")
m_col2.metric("Total Gross Charges Billed", f"${f_df['billed_amount'].sum():,.2f}")
m_col3.metric("Total System Adjudicated Savings", f"${(f_df['billed_amount'].sum() - f_df['allowed_amount'].sum()):,.2f}")
den_rate = (len(f_df[f_df["status"] == "Denied"]) / len(f_df) * 100) if len(f_df) > 0 else 0
m_col4.metric("Engine Denial-to-Submission Ratio", f"{den_rate:.1f}%")

st.markdown("---")

# --- ANALYTICAL CHART CODES ---
c_col1, c_col2 = st.columns(2)

with c_col1:
    st.subheader("📊 Volumetric Breakdown by Status & Demographics")
    if not f_df.empty:
        fig, ax = plt.subplots(figsize=(6,  6))
        f_df.groupby(['status', 'patient_gender']).size().unstack(fill_value=0).plot(kind='bar', stacked=True, ax=ax, color=['#3498db', '#e74c3c', '#95a5a6'])
        ax.set_ylabel("Claim Count")
        plt.xticks(rotation=0)
        st.pyplot(fig)
    else:
        st.write("No data available.")

with c_col2:
    st.subheader("🛑 Engine Clearinghouse Denial Root Causes")
    den_records = f_df[f_df["status"] == "Denied"]
    reasons = den_records["rejection_reason"].value_counts()
    if not reasons.empty:
        fig, ax = plt.subplots(figsize=(6, 6))
        reasons.plot(kind='pie', autopct='%1.1f%%', colors=['#e74c3c', '#e67e22', '#f1c40f', '#34495e'], ax=ax)
        ax.set_ylabel("")
        st.pyplot(fig)
    else:
        st.write("No active rejections match current configuration views.")

# --- RAW TRANSACTION LEDGER ---
st.subheader("📋 Production Grade Clearinghouse Transaction Ledger (Detailed Standard Schema)")
st.dataframe(f_df, use_container_width=True)
