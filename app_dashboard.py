
import streamlit as st
import pandas as pd
import plotly.express as px
from scam_analysis import check_scam_risk

st.set_page_config(page_title="Scamternship Detector Dashboard", layout="wide")
st.title("🚩 Scamternship Detector Dashboard")
st.markdown("""
Analyze internship/job descriptions to identify potential scams, red flags, and suspicious patterns. This tool is part of the #ScamternshipStories initiative by Tech Data Hub.
""")

# Upload CSV
uploaded_file = st.file_uploader("Upload a CSV file with Job Descriptions", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    jd_column = st.selectbox("Select the column containing job descriptions:", df.columns)

    with st.spinner("Analyzing job descriptions..."):
        results = []
        for jd in df[jd_column]:
            if pd.notnull(jd):
                output = check_scam_risk(jd)
                results.append(output)
            else:
                results.append({"score": 0, "flags": [], "advice": "No description provided."})

        df["Scam Score"] = [r["score"] for r in results]
        df["Red Flags"] = [", ".join(r["flags"]) for r in results]
        df["Advice"] = [r["advice"] for r in results]

    st.success("Analysis complete!")
    st.dataframe(df)

    # Visualization
    st.subheader("📊 Scam Score Distribution")
    fig = px.histogram(df, x="Scam Score", nbins=10, color_discrete_sequence=['indianred'])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🧾 Download Results")
    st.download_button(
        label="Download CSV Report",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="scamternship_report.csv",
        mime="text/csv"
    )

else:
    st.info("Please upload a CSV file to begin analysis.")
