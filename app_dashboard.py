import streamlit as st
import pandas as pd
import plotly.express as px
from scam_analysis import check_scam_risk
import io
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np

# Check if pdfplumber is available
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    st.warning("PDF processing disabled - install pdfplumber with: pip install pdfplumber")

st.set_page_config(page_title="Scamternship Detector Dashboard", layout="wide")
st.title("🚩 Scamternship Detector Dashboard")
st.markdown("""
Analyze internship/job descriptions to identify potential scams, red flags, and suspicious patterns. 
This tool is part of the #ScamternshipStories initiative by Tech Data Hub.
""")

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF with error handling"""
    try:
        all_text = []
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text.append(text)
        return "\n".join(all_text)
    except Exception as e:
        st.error(f"PDF processing failed: {str(e)}")
        return None

def analyze_text(text):
    """Split text into potential job descriptions"""
    try:
        # Split by common listing separators
        descriptions = [jd.strip() for jd in re.split(r'\n\d+\.|\n•|\n-|\n○', text) if jd.strip()]
        return descriptions if descriptions else [text]
    except Exception as e:
        st.error(f"Text analysis failed: {str(e)}")
        return [text]

# File Upload
uploaded_file = st.file_uploader("Upload a file with Job Descriptions", 
                               type=["csv"] + (["pdf"] if PDF_SUPPORT else []))

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        if not PDF_SUPPORT:
            st.error("PDF processing not available. Please install pdfplumber.")
            st.stop()
            
        with st.spinner("Extracting text from PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
            if not pdf_text:
                st.stop()
                
            descriptions = analyze_text(pdf_text)
            df = pd.DataFrame({"Job Description": descriptions})
            
    else:  # CSV case
        df = pd.read_csv(uploaded_file)
        jd_column = st.selectbox("Select the column containing job descriptions:", df.columns)
        descriptions = df[jd_column].fillna('').astype(str).tolist()

    # Rest of your analysis code...
    # [Keep all the visualization and analysis code from previous version]

else:
    st.info("Please upload a file to begin analysis.")
    if not PDF_SUPPORT:
        st.markdown("""
        **Note:** For PDF support, install the required package:
        ```bash
        pip install pdfplumber
        ```
        """)
