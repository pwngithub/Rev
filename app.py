
import streamlit as st
import PyPDF2
import pandas as pd
import io

st.set_page_config(page_title="Revenue Report Analyzer", layout="wide")
st.title("📊 Revenue Report Analyzer")

uploaded_file = st.file_uploader("Upload Revenue Report PDF", type=["pdf"])

def parse_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Failed to parse PDF: {e}")
        return ""

def extract_table_rows(text):
    lines = text.splitlines()
    rows = []
    for line in lines:
        parts = line.strip().split("\t")
        if len(parts) >= 4 and parts[1].isdigit():
            rows.append(parts[:4])
    return rows

if uploaded_file:
    raw_text = parse_pdf(uploaded_file)
    rows = extract_table_rows(raw_text)
    if rows:
        df = pd.DataFrame(rows, columns=["Row", "Service", "Last Month", "This Month"])
        for col in ["Last Month", "This Month"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["Change"] = df["This Month"] - df["Last Month"]
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "revenue.csv", "text/csv")
    else:
        st.warning("No rows detected. Check PDF format.")
