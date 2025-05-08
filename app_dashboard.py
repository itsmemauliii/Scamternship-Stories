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
        # Improved column selection logic with better user feedback
        description_column = None
        
        # First try exact match
        if "Description" in df.columns:
            description_column = "Description"
        else:
            # Look for similar columns (case insensitive)
            possible_matches = [col for col in df.columns if "desc" in col.lower()]
            
            if possible_matches:
                # Let user select which column to use
                description_column = st.selectbox(
                    "Select the column containing job descriptions:",
                    options=possible_matches,
                    help="We couldn't find a column named 'Description'. Please select which column contains the job descriptions."
                )
                st.info(f"Using column '{description_column}' for analysis.")
            else:
                # Fallback to first text column with warning
                text_columns = [col for col in df.columns if pd.api.types.is_string_dtype(df[col])]
                
                if text_columns:
                    description_column = text_columns[0]
                    st.warning(
                        f"No obvious description column found. Using '{description_column}' for analysis. "
                        "If this isn't correct, please rename your description column to 'Description' in your data file."
                    )
                else:
                    st.error(
                        "No text columns found for analysis. Please ensure your data contains at least one "
                        "text column with job descriptions."
                    )
                    st.stop()
        
        # Apply scam analysis
        df["Risk Score"] = df[description_column].apply(lambda x: check_scam_risk(str(x)))
        
        # Enhanced visualization with more context
        st.subheader("Risk Score Distribution")
        fig = px.bar(
            df.sort_values("Risk Score", ascending=False),
            x="Job Title" if "Job Title" in df.columns else df.columns[0],
            y="Risk Score",
            color="Company" if "Company" in df.columns else None,
            title="Scam Risk Analysis by Position",
            hover_data=[description_column],
            labels={'x': 'Position', 'y': 'Risk Score (%)'}
        )
        fig.update_layout(
            yaxis_range=[0,100],
            hovermode="closest"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Add summary statistics
        st.subheader("Risk Score Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("High Risk (≥70)", f"{sum(df['Risk Score'] >= 70)}", "positions")
        col2.metric("Medium Risk (30-69)", f"{sum((df['Risk Score'] >= 30) & (df['Risk Score'] < 70))}", "positions")
        col3.metric("Low Risk (<30)", f"{sum(df['Risk Score'] < 30)}", "positions")
        
        # Enhanced results table with filtering
        st.subheader("Detailed Results")
        
        # Add filtering options
        risk_filter = st.slider(
            "Filter by minimum risk score:",
            min_value=0,
            max_value=100,
            value=0,
            help="Show only positions with at least this risk score"
        )
        
        filtered_df = df[df["Risk Score"] >= risk_filter].sort_values("Risk Score", ascending=False)
        
        # Format the display
        display_cols = [description_column, "Risk Score"]
        if "Company" in df.columns:
            display_cols.insert(0, "Company")
        if "Job Title" in df.columns:
            display_cols.insert(0, "Job Title")
        
        # Add explanation of risk scores
        with st.expander("How to interpret risk scores"):
            st.markdown("""
            - **0-29**: Low risk - No obvious red flags detected
            - **30-69**: Medium risk - Some concerning phrases found
            - **70-100**: High risk - Multiple red flags detected
            """)
        
        st.dataframe(
            filtered_df[display_cols],
            column_config={
                "Risk Score": st.column_config.ProgressColumn(
                    "Risk Score",
                    help="Risk score from 0-100",
                    format="%d%%",
                    min_value=0,
                    max_value=100,
                )
            },
            use_container_width=True
        )
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
