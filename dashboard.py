
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Setup
st.set_page_config("📊 FTTH Survey Dashboard", layout="wide")
st.title("📊 FTTH Survey Dashboard - 2025")

# Constants
UPLOAD_DIR = "uploaded_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Upload Section ---
st.sidebar.header("📤 Upload Excel File")
uploaded_file = st.sidebar.file_uploader("Upload new Excel file", type=["xlsx"])

if uploaded_file:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"Uploaded: {uploaded_file.name}")

# --- File Selection Section ---
st.sidebar.header("📁 Manage Uploaded Files")
all_files = sorted([f for f in os.listdir(UPLOAD_DIR) if f.endswith('.xlsx')], reverse=True)
selected_file = st.sidebar.selectbox("Select File to Load", all_files if all_files else ["No files found"], index=0 if all_files else None)

# --- File Deletion ---
if all_files:
    if st.sidebar.button("🗑️ Delete Selected File"):
        os.remove(os.path.join(UPLOAD_DIR, selected_file))
        st.sidebar.success(f"Deleted: {selected_file}")
        st.stop()

# --- Load and Display Data ---
if selected_file and selected_file != "No files found":
    file_path = os.path.join(UPLOAD_DIR, selected_file)
    df = pd.read_excel(file_path, engine="openpyxl")
    st.subheader(f"📄 Previewing: {selected_file}")

    # --- Filters ---
    st.sidebar.header("🔎 Filter Data")
    if 'Location' in df.columns:
        location_options = df['Location'].dropna().unique()
        location_filter = st.sidebar.multiselect("Filter by Location", location_options, default=location_options)

    if 'Category' in df.columns:
        category_options = df['Category'].dropna().unique()
        category_filter = st.sidebar.multiselect("Filter by Category", category_options, default=category_options)

    # Apply filters
    filtered_df = df.copy()
    if 'Location' in df.columns:
        filtered_df = filtered_df[filtered_df['Location'].isin(location_filter)]
    if 'Category' in df.columns:
        filtered_df = filtered_df[filtered_df['Category'].isin(category_filter)]

    # Clean column names
    filtered_df.columns = filtered_df.columns.str.strip()

    # Show filtered data
    st.dataframe(filtered_df, use_container_width=True)

    # --- Revenue Adjustment ---
    if 'Status' in filtered_df.columns and 'MRC' in filtered_df.columns:
        filtered_df['MRC'] = pd.to_numeric(filtered_df['MRC'], errors='coerce')

        filtered_df['Adjusted MRC'] = filtered_df.apply(
            lambda row: -row['MRC'] if str(row['Status']).strip().lower() == 'disconnect' else row['MRC'],
            axis=1
        )
        revenue_summary = filtered_df.groupby('Status')['Adjusted MRC'].sum().reset_index()
        revenue_summary.columns = ['Status', 'Net MRC Change ($)']

        st.subheader("💵 Revenue Change by Status (Filtered)")
        st.dataframe(revenue_summary, use_container_width=True)
        st.metric("📈 Net Monthly Revenue Change", f"${filtered_df['Adjusted MRC'].sum():,.2f}")
    else:
        st.warning("Missing 'Status' or 'MRC' columns for revenue analysis.")
else:
    st.info("No Excel files uploaded yet. Use the sidebar to upload one.")
