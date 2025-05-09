import streamlit as st
import pandas as pd
import plotly.express as px
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PyPDF2 import PdfReader
import openai
import os

# **Initialize OpenAI API Key**
openai_api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    st.warning("OpenAI API key not found. Please add it to Streamlit secrets or environment variables for GenAI features.")

def analyze_with_genai(text, api_key):
    """Analyzes text using OpenAI's GPT model for potential scam indicators."""
    if not api_key:
        return "API key not configured for GenAI analysis."
    try:
        openai.api_key = api_key
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes job descriptions for potential scam indicators. Focus on vague language, requests for money, guaranteed roles without interviews, and unusual urgency."},
                {"role": "user", "content": f"Analyze the following text for scam indicators: '{text}'"}
            ],
            temperature=0.7,
            max_tokens=150,
            n=1,
            stop=None,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error during GenAI analysis: {e}"

def check_scam_risk(text):
    """Checks text for common scam indicators and returns a risk score."""
    risk_score = 0
    text = str(text).lower()
    red_flags = {
        "no payment": 15, "unpaid": 15, "deposit required": 25, "send money": 25,
        "guaranteed job": 20, "immediate start": 10, "no experience needed": 10,
        "registration fee": 20, "training fee": 20, "investment required": 25,
        "pay to work": 30, "application fee": 20
    }
    for flag, score in red_flags.items():
        if flag in text:
            risk_score += score
    if re.search(r"\$\d+|\d+\s*(usd|inr|₹|dollars|rupees)", text):
        risk_score += 25
    return min(risk_score, 100)

def generate_wordcloud(text):
    """Generates a word cloud from the given text."""
    try:
        wordcloud = WordCloud(width=1000, height=600, background_color="white",
                            colormap="Reds", max_words=100, stopwords=None,
                            contour_width=1, contour_color='steelblue').generate(text)
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        plt.tight_layout()
        return fig
    except Exception as e:
        st.error(f"Word cloud generation failed: {e}")
        return None

def load_data(uploaded_file):
    """Loads data from CSV or Excel file."""
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, skipinitialspace=True)
        elif uploaded_file.name.endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a CSV or Excel file.")
            return None
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def load_pdf_data(uploaded_file):
    """Loads text data from a PDF file."""
    text = ""
    try:
        pdf_reader = PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        # Basic extraction (can be improved)
        df = pd.DataFrame({"Description": [text]})
        return df
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# **Main App**
st.set_page_config(page_title="Scamternship Detector", layout="wide")
st.title("Scamternship Detector Dashboard")

uploaded_file = st.file_uploader("Upload CSV, Excel, or PDF file containing internship listings",
                                 type=["csv", "xls", "xlsx", "pdf"])

if uploaded_file is not None:
    if uploaded_file.name.endswith(".pdf"):
        df = load_pdf_data(uploaded_file)
    else:
        df = load_data(uploaded_file)

    if df is not None and not df.empty:
        st.subheader("Uploaded Data")
        st.dataframe(df.head())

        description_cols = [col for col in df.columns if pd.api.types.is_string_dtype(df[col])]
        if not description_cols:
            st.warning("No text columns found for analysis.")
        else:
            description_column = st.selectbox("Select the column containing descriptions:", description_cols)

            if description_column:
                df["Risk Score"] = df[description_column].apply(check_scam_risk)
                df["Risk Level"] = pd.cut(df["Risk Score"], bins=[0, 30, 70, 100],
                                            labels=["Low", "Medium", "High"], right=False)

                st.subheader("Analysis Results")
                st.dataframe(df[["Description", "Risk Score", "Risk Level"]].sort_values(by="Risk Score", ascending=False))

                # GenAI Analysis Option
                if openai_api_key:
                    use_genai = st.checkbox("Use GenAI for deeper analysis of descriptions")
                    if use_genai:
                        with st.spinner("Running GenAI analysis..."):
                            df["GenAI Analysis"] = df[description_column].apply(lambda text: analyze_with_genai(text, openai_api_key))
                            st.subheader("GenAI Analysis Results")
                            st.dataframe(df[["Description", "Risk Score", "Risk Level", "GenAI Analysis"]].sort_values(by="Risk Score", ascending=False))

                # Word Cloud
                st.subheader("Red Flags Word Cloud")
                all_descriptions = " ".join(df[description_column].astype(str).fillna(""))
                if all_descriptions:
                    wordcloud_fig = generate_wordcloud(all_descriptions)
                    if wordcloud_fig:
                        st.pyplot(wordcloud_fig)
                    else:
                        st.warning("Could not generate word cloud.")
                else:
                    st.info("No description text available for word cloud.")

                # Red Flag Term Frequency
                st.subheader("Red Flag Term Frequency")
                red_flag_terms = ["payment", "deposit", "fee", "unpaid", "money", "investment",
                                    "registration", "training", "guaranteed", "required", "pay",
                                    "send", "secure", "opportunity"]
                term_counts = {}
                for term in red_flag_terms:
                    term_counts[term] = df[description_column].astype(str).str.lower().str.contains(r'\b' + re.escape(term) + r'\b').sum()

                term_df = pd.DataFrame(term_counts.items(), columns=['Term', 'Count']).sort_values(by='Count', ascending=False)
                st.dataframe(term_df)

                # Example Listings
                st.subheader("View Examples by Risk Level")
                risk_level_filter = st.multiselect("Filter by Risk Level", ["Low", "Medium", "High"], default=["High"])
                filtered_examples = df[df["Risk Level"].isin(risk_level_filter)][["Description", "Risk Score", "Risk Level"]]
                st.dataframe(filtered_examples)

    else:
        st.info("Please upload a file to begin analysis.")
