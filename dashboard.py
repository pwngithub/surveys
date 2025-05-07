
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os
from datetime import datetime

st.title("📊 Monthly Customer Activity Dashboard")

# --- File Upload ---
UPLOAD_DIR = "uploaded_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.sidebar.header("📤 Upload New Monthly File")
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsm"])

if uploaded_file and "just_uploaded" not in st.session_state:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{uploaded_file.name}")
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.just_uploaded = True
    st.rerun()

# --- List and sort uploaded files ---
st.sidebar.header("📂 Stored Files")
all_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".xlsm")]
sort_order = st.sidebar.radio("Sort by", options=["Newest First", "Oldest First"])
available_files = sorted(all_files, reverse=(sort_order == "Newest First"))

if not available_files:
    st.warning("No uploaded files available.")
    st.stop()

# --- Select file ---
selected_file = st.sidebar.selectbox("Choose a file to analyze", available_files)
selected_file_path = os.path.join(UPLOAD_DIR, selected_file)

# --- File preview ---
with st.expander("📄 Preview First 5 Rows"):
    try:
        preview_df = pd.read_excel(selected_file_path, sheet_name="Sheet1", nrows=5)
        st.dataframe(preview_df)
    except Exception as e:
        st.error(f"Could not preview file: {e}")

# --- Delete file ---
if st.sidebar.button("🗑️ Delete Selected File"):
    os.remove(selected_file_path)
    st.success(f"Deleted: {selected_file}")
    st.experimental_rerun()

# --- Load and display ---
st.subheader(f"📂 Analyzing File: `{selected_file}`")
xls = pd.ExcelFile(selected_file_path)
data = xls.parse('Sheet1')

# --- Data Prep ---
data["MRC"] = pd.to_numeric(data["MRC"], errors="coerce")
data["Submission Date"] = pd.to_datetime(data["Submission Date"], errors="coerce")

# --- Filters ---
st.sidebar.header("🔍 Filters")
min_date, max_date = data["Submission Date"].min(), data["Submission Date"].max()
start_date, end_date = st.sidebar.date_input("Submission Date Range", [min_date, max_date])
filtered_data = data[
    (data["Submission Date"] >= pd.Timestamp(start_date)) &
    (data["Submission Date"] <= pd.Timestamp(end_date))
]

status_options = ["All"] + sorted(filtered_data["Status"].dropna().unique().tolist())
selected_status = st.sidebar.selectbox("Status", status_options)
if selected_status != "All":
    filtered_data = filtered_data[filtered_data["Status"] == selected_status]

reason_options = ["All"] + sorted(filtered_data["Reason"].dropna().unique().tolist())
selected_reason = st.sidebar.selectbox("Reason", reason_options)
if selected_reason != "All":
    filtered_data = filtered_data[filtered_data["Reason"] == selected_reason]

customer_search = st.sidebar.text_input("Search Customer Name")
if customer_search:
    filtered_data = filtered_data[filtered_data["Customer Name"].str.contains(customer_search, case=False, na=False)]

# --- Totals ---
st.header("📌 Overall Totals")
total_summary = filtered_data.groupby("Status").agg(Count=("Status", "count")).reset_index()
adjusted_mrc = filtered_data.copy()
adjusted_mrc["MRC"] = adjusted_mrc.apply(
    lambda row: -row["MRC"] if row["Status"] == "Disconnect" else row["MRC"],
    axis=1
)
total_mrc = adjusted_mrc["MRC"].sum()
st.dataframe(total_summary)
st.metric("Net MRC", f"${total_mrc:,.2f}")

# --- Churn Summary ---
st.header("⚠️ Churn Summary by Reason")
churn_df = filtered_data[filtered_data["Status"] == "Disconnect"]
churn_summary = churn_df.groupby("Reason").agg(Count=("Reason", "count")).reset_index()
churn_total_mrc = churn_df["MRC"].sum()
st.dataframe(churn_summary)
st.metric("Churn Total MRC", f"${churn_total_mrc:,.2f}")

# --- Churn by Location ---
st.header("📍 Churn by Location")
loc_summary = churn_df.groupby("Location").agg(Count=("Location", "count")).sort_values(by="Count", ascending=False).reset_index()
st.dataframe(loc_summary)

# --- Visualizations ---
st.header("📊 Visualizations")

fig1, ax1 = plt.subplots()
ax1.barh(churn_summary["Reason"], churn_summary["Count"])
ax1.set_title("Churn Count by Reason")
st.pyplot(fig1)

fig2, ax2 = plt.subplots()
ax2.bar(loc_summary["Location"], loc_summary["Count"])
ax2.set_title("Churn Count by Location")
ax2.tick_params(axis='x', rotation=90)
st.pyplot(fig2)

fig3, ax3 = plt.subplots()
category_counts = filtered_data["Status"].value_counts()
category_counts.plot(kind="pie", autopct='%1.1f%%', ax=ax3)
ax3.set_ylabel("")
ax3.set_title("Customer Status Breakdown")
st.pyplot(fig3)

# --- Trend Chart ---
st.header("📈 Daily Activity Trend")
daily_trend = filtered_data.groupby(["Submission Date", "Status"]).size().unstack(fill_value=0)
st.line_chart(daily_trend)

# --- Status Breakdown ---
st.header("📊 Status Breakdown: New, Converted, Previous")
filtered_statuses = filtered_data[filtered_data["Status"].isin(["NEW", "Convert", "Previous"])]
status_counts = filtered_statuses["Status"].value_counts().reset_index()
status_counts.columns = ["Status", "Count"]

fig_status, ax_status = plt.subplots()
ax_status.bar(status_counts["Status"], status_counts["Count"])
ax_status.set_title("New vs Converted vs Previous Customers")
st.pyplot(fig_status)

# --- New by Location ---
if selected_status == "NEW":
    st.header("📍 New Customers by Location (Filtered)")
    new_by_location = filtered_data.groupby("Location").size().sort_values(ascending=False).reset_index(name="Count")

    fig_new, ax_new = plt.subplots()
    ax_new.bar(new_by_location["Location"], new_by_location["Count"])
    ax_new.set_title("New Customer Count by Location")
    ax_new.tick_params(axis='x', rotation=90)
    st.pyplot(fig_new)
