
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Revenue Report Analyzer", layout="wide")

st.title("📊 Revenue Report Analyzer")

uploaded_file = st.file_uploader("Upload Revenue CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Clean dollar fields
    for col in ["AUT Amount", "MAN Amount", "ADJ Amount", "Total Amount"]:
        df[col] = df[col].astype(str).str.replace("[$,()]", "", regex=True).str.replace(")", "", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Net Change"] = df["Sub Count End"] - df["Sub Count Start"]

    st.subheader("📌 Summary Metrics")
    total_rev = df["Total Amount"].sum()
    total_net_change = df["Net Change"].sum()
    st.metric("Total Revenue", f"${total_rev:,.2f}")
    st.metric("Total Subscriber Net Change", int(total_net_change))

    st.subheader("📈 Top Movers")
    top_movers = df[["Pkg Name", "Sub Count Start", "Sub Count End", "Net Change"]].sort_values("Net Change", ascending=False)
    st.dataframe(top_movers, use_container_width=True)

    st.subheader("📂 Revenue Breakdown by Section")
    section_summary = df.groupby("Section").agg(
        Revenue_Total=pd.NamedAgg(column="Total Amount", aggfunc="sum"),
        Subscriber_Change=pd.NamedAgg(column="Net Change", aggfunc="sum")
    ).sort_values("Revenue_Total", ascending=False)
    st.dataframe(section_summary, use_container_width=True)

    st.download_button("📥 Download Cleaned CSV", df.to_csv(index=False), file_name="cleaned_revenue_report.csv")
else:
    st.info("Please upload a CSV file to begin.")
