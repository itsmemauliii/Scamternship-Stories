import streamlit as st
import pandas as pd
import plotly.express as px
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# **IMPORTANT: `st.set_page_config()` MUST be the very first Streamlit call.**
st.set_page_config(page_title="Scamternship Detector Dashboard", layout="wide")

# Initialize tabs
tab1, tab2, tab3 = st.tabs(["Data Upload", "Analysis Results", "Red Flags Word Cloud"])

# Sample data - replace with your actual data loading logic
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "Job Title": ["Marketing Intern", "Data Analyst", "Remote Assistant", "Software Engineer"],
        "Company": ["ABC Corp", "XYZ Inc", "Home Based Jobs", "Tech Innovators"],
        "Description": [
            "Great learning opportunity with no payment required",
            "Data analysis position with competitive salary",
            "Send $500 deposit to secure your remote position",
            "Internship program with certificate upon completion"
        ]
    })

def check_scam_risk(text):
    """
    Simplified version of scam detection for the dashboard
    """
    risk_score = 0
    text = text.lower()
    
    red_flags = [
        "no payment", "unpaid", "deposit required", "send money",
        "guaranteed job", "immediate start", "no experience needed",
        "registration fee", "training fee", "investment required"
    ]
    
    for flag in red_flags:
        if flag in text:
            risk_score += 10
    
    if re.search(r"\$\d+|\d+\s*(USD|INR|₹)", text):
        risk_score += 20
        
    return min(risk_score, 100)  # Cap at 100

def generate_wordcloud(text):
    """Generate word cloud visualization"""
    try:
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color="white",
            colormap="Reds",
            max_words=50,
        ).generate(text)
        
        fig, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        return fig
    except Exception as e:
        st.error(f"Word cloud generation failed: {str(e)}")
        return None

def load_data(uploaded_file):
    """Loads data from the uploaded file"""
    try:
        if uploaded_file.name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith((".xls", ".xlsx")):
            return pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a CSV or Excel file.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

with tab1:
    st.header("Upload Your Data")
    uploaded_file = st.file_uploader(
        "Choose a file (CSV or Excel)",
        type=["csv", "xls", "xlsx"],
        help="Upload internship listings for analysis"
    )

    if uploaded_file:
        df = load_data(uploaded_file)
        if not df.empty:
            st.session_state.df = df
            st.success("Data loaded successfully!")
            st.dataframe(df.head())

with tab2:
    st.header("Analysis Results")
    df = st.session_state.df
    
    if not df.empty:
        # Ensure we have a description column to analyze
        if "Description" not in df.columns:
            st.warning("No 'Description' column found. Using first text column instead.")
            text_columns = [col for col in df.columns if df[col].dtype == 'object']
            if text_columns:
                df["Description"] = df[text_columns[0]]
            else:
                st.error("No text columns found for analysis.")
                st.stop()
        
        # Apply scam analysis
        df["Risk Score"] = df["Description"].apply(lambda x: check_scam_risk(str(x)))
        
        # Visualize results
        fig = px.bar(
            df.sort_values("Risk Score", ascending=False),
            x="Job Title" if "Job Title" in df.columns else df.columns[0],
            y="Risk Score",
            color="Company" if "Company" in df.columns else None,
            title="Scam Risk Analysis"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show detailed results
        st.dataframe(df.sort_values("Risk Score", ascending=False))

with tab3:
    st.header("Red Flags Word Cloud")
    df = st.session_state.df
    
    if not df.empty and "Description" in df.columns:
        all_text = " ".join(df["Description"].astype(str))
        wc_fig = generate_wordcloud(all_text)
        
        if wc_fig:
            st.pyplot(wc_fig)
        else:
            st.info("Could not generate word cloud. Here are common terms:")
            words = re.findall(r"\b\w{4,}\b", all_text.lower())
            word_counts = pd.Series(words).value_counts().head(10)
            st.bar_chart(word_counts)
    else:
        st.warning("No description data available to generate word cloud.")
