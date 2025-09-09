
import streamlit as st
import pandas as pd
import numpy as np
import io
from PyPDF2 import PdfReader
import re

st.set_page_config(page_title="Revenue Report Analyzer", layout="wide")
st.title("📊 Revenue Report Analyzer")

def _to_int(x):
    try:
        return int(str(x).replace(",", "").strip())
    except Exception:
        return None

def _money_to_float(s: str, parentheses_as_negative=True):
    if s is None:
        return None
    txt = str(s).strip().replace(",", "")
    if txt == "" or txt.upper() == "NAN":
        return None
    neg = False
    if parentheses_as_negative and txt.startswith("(") and txt.endswith(")"):
        neg = True
        txt = txt[1:-1]
    txt = txt.replace("$", "")
    try:
        val = float(txt)
    except Exception:
        try:
            val = float(txt.replace("−", "-"))
        except Exception:
            return None
    return -val if neg else val

def extract_rows(pdf_bytes: bytes, use_service_dedup=False):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "\n".join([p.extract_text() or "" for p in reader.pages])
    csv_blocks = re.findall(r'\[CsvExport[^\]]*\]"(.+?)"\s*$', text, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
    fallback = re.compile(
        r'^(?P<code>[A-Z0-9\-\s]{1,12})\s+(?P<service>.+?)\s+'
        r'(?P<start>\-?\d+)\s+(?P<end>\-?\d+)\s+(?P<chg>\-?\d+).*?'
        r'\$?(?P<rev>[\(\)\d\.,\-]+)',
        re.IGNORECASE
    )
    rows = []

    for block in csv_blocks:
        try:
            flds = next(pd.read_csv(io.StringIO(block), header=None).itertuples(index=False))
            rows.append({
                "Code": str(flds[1]).strip(),
                "Service": str(flds[2]).strip(),
                "Start Subs": _to_int(flds[3]),
                "End Subs": _to_int(flds[4]),
                "Change": _to_int(flds[5]),
                "Revenue": flds[-1]
            })
        except:
            continue

    for line in text.splitlines():
        m = fallback.search(line.strip())
        if m:
            rows.append({
                "Code": m.group("code").strip(),
                "Service": m.group("service").strip(),
                "Start Subs": _to_int(m.group("start")),
                "End Subs": _to_int(m.group("end")),
                "Change": _to_int(m.group("chg")),
                "Revenue": m.group("rev")
            })

    df = pd.DataFrame(rows).dropna(how="all")
    if not df.empty:
        df["Revenue"] = df["Revenue"].apply(_money_to_float)
        dedup_cols = ["Code", "Start Subs", "End Subs", "Change"]
        if use_service_dedup:
            dedup_cols.insert(1, "Service")
        df = df.drop_duplicates(subset=dedup_cols)
    return df, text

uploaded = st.file_uploader("Upload Revenue Report PDF", type=["pdf"])
use_dedup = st.checkbox("Use Service in de-duplication", value=False)

if uploaded:
    try:
        pdf_bytes = uploaded.read()
        df, raw_text = extract_rows(pdf_bytes, use_service_dedup=use_dedup)

        if df.empty:
            st.warning("No rows extracted. Check formatting or contact support.")
            with st.expander("📄 Raw text preview"):
                st.text(raw_text[:12000])
        else:
            st.subheader("📈 Summary")
            df["Net Adds"] = df["End Subs"].fillna(0) - df["Start Subs"].fillna(0)
            st.metric("Total Revenue", f"${df['Revenue'].sum(skipna=True):,.2f}")
            st.metric("Total Subscribers", f"{int(df['End Subs'].sum(skipna=True)):,}")

            st.subheader("📊 Top Revenue Services")
            st.dataframe(df.sort_values("Revenue", ascending=False).head(10))

            st.subheader("📈 Biggest Net Adds")
            st.dataframe(df.sort_values("Net Adds", ascending=False).head(10))

            st.subheader("📉 Largest Declines")
            st.dataframe(df.sort_values("Net Adds", ascending=True).head(10))

            st.subheader("🧾 Full Table")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", data=csv, file_name="revenue_output.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Something went wrong parsing the PDF: {e}")
else:
    st.info("Please upload a PDF to begin.")
