from genai_analysis import analyze_with_genai
import streamlit as st
import openai
import os
import pandas as pd
import plotly.express as px
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PyPDF2 import PdfReader

# **DEBUGGING: Check if Streamlit secrets are loaded**
print("DEBUG: app_dashboard - Checking Streamlit secrets...")
try:
    openai_api_key_from_secrets = st.secrets.get("OPENAI_API_KEY")
    if openai_api_key_from_secrets:
        print(f"DEBUG: app_dashboard - OpenAI API Key found in secrets (first 8 chars): {openai_api_key_from_secrets[:8]}")
    else:
        print("DEBUG: app_dashboard - OpenAI API Key NOT FOUND in secrets within app_dashboard!")
except Exception as e:
    print(f"DEBUG: app_dashboard - Error accessing secrets: {e}")

# **IMPORTANT: st.set_page_config() MUST be the very first Streamlit call.**
st.set_page_config(page_title="Scamternship Detector Dashboard", layout="wide")

# Initialize session state
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
# Define functions
def check_scam_risk(text):
    """
    Enhanced version of scam detection for the dashboard
    """
    risk_score = 0
    text = str(text).lower()

    red_flags = {
        "no payment": 15,
        "unpaid": 15,
        "deposit required": 25,
        "send money": 25,
        "guaranteed job": 20,
        "immediate start": 10,
        "no experience needed": 10,
        "registration fee": 20,
        "training fee": 20,
        "investment required": 25,
        "pay to work": 30,
        "application fee": 20
    }

    for flag, score in red_flags.items():
        if flag in text:
            risk_score += score

    if re.search(r"\$\d+|\d+\s*(USD|INR|₹|dollars|rupees)", text):
        risk_score += 25

    return min(risk_score, 100)  # Cap at 100

def generate_wordcloud(text):
    """Generate word cloud visualization with improved settings"""
    try:
        wordcloud = WordCloud(
            width=1000,
            height=600,
            background_color="white",
            colormap="Reds",
            max_words=100,
            stopwords=None,
            contour_width=1,
            contour_color='steelblue'
        ).generate(text)

        fig, ax = plt.subplots(figsize=(12, 8))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        plt.tight_layout()
        return fig
    except Exception as e:
        st.error(f"Word cloud generation failed: {str(e)}")
        return None

def load_data(uploaded_file):
    """Load data from CSV or Excel file."""
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, skipinitialspace=True)
        elif uploaded_file.name.endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a CSV or Excel file.")
            return None
        if not df.empty:
            return df
        else:
            st.error("The file is empty")
            return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def load_pdf_data(uploaded_file):
    """Load data from PDF file and extract relevant information."""
    text = ""
    try:
        pdf_reader = PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        # Basic extraction (Improved)
        job_title_match = re.search(r"(?:Job Title:|Position:)\s*(.*)", text, re.IGNORECASE)
        job_title = job_title_match.group(1).strip() if job_title_match else "N/A"

        company_match = re.search(r"(?:Company:|Hiring at:|Organization:)\s*(.*)", text, re.IGNORECASE)
        company = company_match.group(1).strip() if company_match else "N/A"
        return pd.DataFrame({"Job Title": [job_title], "Companies": [company], "Description": [text]})

    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# Main App Structure
tab1, tab2, tab3 = st.tabs(["Data Upload", "Analysis Results", "Red Flags Word Cloud"])

with tab1:
    st.header("Upload Your Data")
    uploaded_file = st.file_uploader(
        "Choose a file (CSV, Excel, or PDF)",
        type=["csv", "xls", "xlsx", "pdf"],
        help="Upload internship listings for analysis"
    )

    if uploaded_file:
        if uploaded_file.name.endswith(".pdf"):
            df = load_pdf_data(uploaded_file)
        else:
            df = load_data(uploaded_file)

        if df is not None and not df.empty:
            st.session_state.df = df
            st.success("Data loaded successfully!")

            # Show basic stats
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Listings", len(df))
            text_cols = [col for col in df.columns if pd.api.types.is_string_dtype(df[col])]
            col2.metric("Text Columns", len(text_cols))
            col3.metric("Companies", df["Companies"].nunique() if "Companies" in df.columns else "N/A")

            st.dataframe(df.head())
        else:
            st.warning("Could not load data from the file.")

with tab2:
    st.header("Analysis Results")
    df = st.session_state.df

    if not df.empty:
        # Improved column selection for description
        description_column = None
        text_columns = [col for col in df.columns if pd.api.types.is_string_dtype(df[col])]

        if "Description" in df.columns:
            description_column = "Description"
        elif text_columns:
            if len(text_columns) > 1:
                description_column = st.selectbox(
                    "Select the description column:",
                    text_columns,
                    index=0,
                    help="Select which column contains the job descriptions"
                )
            else:
                description_column = text_columns[0]
                st.warning(f"Using '{description_column}' as description column")
        else:
            st.error("No text columns found for analysis")
            st.stop()

        use_genai = st.checkbox("Use GenAI for deeper analysis", value=False)
        if use_genai:
            with st.spinner("Running GenAI analysis..."):
                openai_api_key_from_secrets = st.secrets.get("OPENAI_API_KEY")
                df["GenAI Analysis"] = df[description_column].apply(lambda text: analyze_with_genai(text, openai_api_key_from_secrets))

        # Safely display results with available columns
        st.subheader("Final Results Table")
        expected_cols = ["Job Title", "Companies", description_column, "Risk Score", "Risk Level", "GenAI Analysis"]
        available_cols = [col for col in expected_cols if col in df.columns]
        st.dataframe(df[available_cols])


        # **New: Column selection for Job Title/Position**
        job_title_column = None
        all_columns = df.columns.tolist()
        if "Job Title" in all_columns:
            job_title_column = "Job Title"
        elif all_columns:
            job_title_column = st.selectbox(
                "Select the job title/position column:",
                all_columns,
                index=0,
                help="Select which column contains the job titles or position names"
            )

        if not job_title_column:
            st.warning("No column selected for job titles/positions. Position-wise analysis will use row index.")

        # Apply enhanced scam analysis
        with st.spinner("Analyzing listings for potential scams..."):
            df["Risk Score"] = df[description_column].apply(check_scam_risk)
            df["Risk Level"] = pd.cut(df["Risk Score"],
                                        bins=[0, 30, 70, 100],
                                        labels=["Low", "Medium", "High"],
                                        right=False)

        # Visualization Section
        st.subheader("Risk Analysis Visualizations")

        # Tabbed view for different perspectives
        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["By Position", "By Company", "Risk Distribution"])

        with viz_tab1:
            # Position-wise risk chart
            x_axis_label = job_title_column if job_title_column else df.index
            fig1 = px.bar(
                df.sort_values("Risk Score", ascending=False),
                x=x_axis_label,
                y="Risk Score",
                color="Risk Level",
                color_discrete_map={"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e74c3c"},
                hover_data=[description_column, "Companies"] if "Companies" in df.columns else [description_column],
                title="Risk Scores by Position",
                labels={"Risk Score": "Risk Score (%)", x_axis_label: "Position"},
                height=600
            )
            fig1.update_layout(
                xaxis_title="Position",
                yaxis_range=[0, 100],
                hovermode="closest"
            )
            st.plotly_chart(fig1, use_container_width=True)

        with viz_tab2:
            if "Companies" in df.columns:
                # Company-wise analysis
                company_stats = df.groupby("Companies").agg(
                    Avg_Risk=("Risk Score", "mean"),
                    Count=("Risk Score", "count"),
                    High_Risk=("Risk Level", lambda x: sum(x == "High"))
                )
                company_stats = company_stats.sort_values("Avg_Risk", ascending=False)

                fig2 = px.scatter(
                    company_stats,
                    x="Count",
                    y="Avg_Risk",
                    size="High_Risk",
                    color="Avg_Risk",
                    color_continuous_scale="reds",
                    hover_name=company_stats.index,
                    title="Company Risk Profile (Size = High Risk Count)",
                    labels={"Avg_Risk": "Average Risk", "Count": "Listings Count", "Companies": "Company"},
                    height=600
                )
                fig2.update_layout(
                    yaxis_range=[0, 100],
                    xaxis_range=[0, company_stats["Count"].max() * 1.1]
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Company information not available for this analysis")

        with viz_tab3:
            # Risk distribution visualization
            col1, col2 = st.columns(2)

            with col1:
                # Pie chart
                risk_dist = df["Risk Level"].value_counts().reset_index()
                fig3 = px.pie(
                    risk_dist,
                    values="count",
                    names="Risk Level",
                    color="Risk Level",
                    color_discrete_map={"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e74c3c"},
                    hole=0.3,
                    title="Risk Level Distribution"
                )
                st.plotly_chart(fig3, use_container_width=True)

            with col2:
                # Histogram
                fig4 = px.histogram(
                    df,
                    x="Risk Score",
                    nbins=20,
                    color="Risk Level",
                    color_discrete_map={"Low": "#2ecc71", "Medium": "#f39c12", "High": "#e74c3c"},
                    title="Risk Score Distribution",
                    labels={"Risk Score": "Risk Score (%)"}
                )
                st.plotly_chart(fig4, use_container_width=True)

        # Detailed Results Section
        st.subheader("Detailed Analysis Results")

        # Filter controls
        with st.expander("Filter Options"):
            min_score = st.slider("Minimum Risk Score", 0, 100, 0)
            risk_level = st.multiselect(
                "Risk Level",
                options=["Low", "Medium", "High"],
                default=["High", "Medium"]
            )

        # Apply filters
        filtered_df = df[
            (df["Risk Score"] >= min_score) &
            (df["Risk Level"].isin(risk_level))
        ].sort_values("Risk Score", ascending=False)

        # Show metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Filtered Listings", len(filtered_df))
        col2.metric("Average Risk", f"{filtered_df['Risk Score'].mean():.1f}%")
        col3.metric("High Risk", f"{sum(filtered_df['Risk Level'] == 'High')}")

        # Display results
        st.dataframe(
            filtered_df.style.applymap(
                lambda x: "background-color: #ffe6e6" if x == "High" else
                          ("background-color: #fff2e6" if x == "Medium" else ""),
                subset=["Risk Level"]
            ),
            column_config={
                "Risk Score": st.column_config.ProgressColumn(
                    "Risk Score",
                    format="%d%%",
                    min_value=0,
                    max_value=100
                )
            },
            use_container_width=True,
            height=600
        )

with tab3:
    st.header("Red Flags Analysis")
    df = st.session_state.df

    if not df.empty:
        # Improved column selection for description
        description_column = None
        text_columns = [col for col in df.columns if pd.api.types.is_string_dtype(df[col])]

        if "Description" in df.columns:
            description_column = "Description"
        elif text_columns:
            if len(text_columns) > 1:
                description_column = st.selectbox(
                    "Select the description column:",
                    text_columns,
                    index=0,
                    help="Select which column contains the job descriptions"
                )
            else:
                description_column = text_columns[0]
                st.warning(f"Using '{description_column}' as description column")
        else:
            st.error("No text columns found for analysis")
            st.stop()

        # Enhanced word cloud section
        st.subheader("Word Cloud of Common Terms")

        all_text = " ".join(df[description_column].astype(str))
        wc_fig = generate_wordcloud(all_text)

        if wc_fig:
            st.pyplot(wc_fig)
        else:
            st.warning("Could not generate word cloud")

        # Term frequency analysis
        st.subheader("Red Flag Term Frequency")

        red_flag_terms = [
            "payment", "deposit", "fee", "unpaid", "money",
            "investment", "registration", "training", "guaranteed",
            "required", "pay", "send", "secure", "opportunity"
        ]

        term_counts = {}
        for term in red_flag_terms:
            term_counts[term] = sum(
                bool(re.search(rf"\b{term}\b", text.lower()))
                for text in df[description_column].astype(str)
            )

        term_df = pd.DataFrame.from_dict(term_counts, orient="index", columns=["Count"])
        term_df = term_df.sort_values("Count", ascending=False)

        fig5 = px.bar(
            term_df,
            x=term_df.index,
            y="Count",
            color="Count",
            color_continuous_scale="reds",
            title="Red Flag Term Frequency",
            labels={"index": "Term", "Count": "Occurrences"}
        )
        st.plotly_chart(fig5, use_container_width=True)

        # Show examples for selected term
        selected_term = st.selectbox(
            "View examples containing term:",
            term_df.index,
            index=0
        )

        examples = df[
            df[description_column].str.contains(selected_term, case=False)
        ][["Description", "Risk Score", "Risk Level"]]  # Ensure 'Description' is used here

        if not examples.empty:
            st.subheader(f"Examples containing '{selected_term}'")
            st.dataframe(examples, use_container_width=True)
        else:
            st.info(f"No examples found containing '{selected_term}'")
    else:
        st.warning("No description data available for analysis")
