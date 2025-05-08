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
        # [Previous column selection logic remains the same...]
        
        # Apply scam analysis
        df["Risk Score"] = df[description_column].apply(lambda x: check_scam_risk(str(x)))
        df["Risk Level"] = pd.cut(df["Risk Score"],
                                 bins=[0, 30, 70, 100],
                                 labels=["Low", "Medium", "High"],
                                 right=False)
        
        # 1. Enhanced Risk Distribution Chart
        st.subheader("Risk Distribution Overview")
        
        # Create tabs for different chart views
        chart_tab1, chart_tab2, chart_tab3 = st.tabs(["By Position", "By Company", "Risk Levels"])
        
        with chart_tab1:
            # Interactive bar chart with more features
            fig1 = px.bar(
                df.sort_values("Risk Score", ascending=False),
                x="Job Title" if "Job Title" in df.columns else df.columns[0],
                y="Risk Score",
                color="Risk Level",
                color_discrete_map={
                    "Low": "#2ecc71",
                    "Medium": "#f39c12",
                    "High": "#e74c3c"
                },
                hover_data=[description_column, "Company"] if "Company" in df.columns else [description_column],
                title="Risk Scores by Position",
                labels={'x': 'Position', 'y': 'Risk Score (%)'},
                height=500
            )
            fig1.update_layout(
                xaxis={'categoryorder':'total descending'},
                yaxis_range=[0,100],
                hoverlabel=dict(bgcolor="white", font_size=12),
                uniformtext_minsize=8,
                uniformtext_mode='hide'
            )
            fig1.update_traces(
                marker_line_color='rgb(8,48,107)',
                marker_line_width=1.5,
                opacity=0.9
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with chart_tab2:
            if "Company" in df.columns:
                # Company-wise aggregation
                company_df = df.groupby("Company", as_index=False).agg(
                    Avg_Risk=("Risk Score", "mean"),
                    Positions=("Job Title", "count")
                ).sort_values("Avg_Risk", ascending=False)
                
                fig2 = px.scatter(
                    company_df,
                    x="Company",
                    y="Avg_Risk",
                    size="Positions",
                    color="Avg_Risk",
                    color_continuous_scale="RdYlGn_r",
                    hover_name="Company",
                    hover_data=["Positions"],
                    title="Average Risk by Company (Size = # of Positions)",
                    labels={'Avg_Risk': 'Average Risk Score', 'Company': ''},
                    height=500
                )
                fig2.update_layout(
                    yaxis_range=[0,100],
                    coloraxis_showscale=False,
                    xaxis={'tickangle': 45}
                )
                fig2.update_traces(
                    marker=dict(line=dict(width=1, color='DarkSlateGrey'))
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Company information not available for this view")
        
        with chart_tab3:
            # Pie chart showing risk level distribution
            risk_counts = df["Risk Level"].value_counts().reset_index()
            risk_counts.columns = ["Risk Level", "Count"]
            
            fig3 = px.pie(
                risk_counts,
                values="Count",
                names="Risk Level",
                color="Risk Level",
                color_discrete_map={
                    "Low": "#2ecc71",
                    "Medium": "#f39c12",
                    "High": "#e74c3c"
                },
                hole=0.4,
                title="Distribution of Risk Levels",
                hover_data=["Count"],
                labels={"Count": "Positions"}
            )
            fig3.update_traces(
                textposition='inside',
                textinfo='percent+label',
                pull=[0.1 if level == "High" else 0 for level in risk_counts["Risk Level"])
            st.plotly_chart(fig3, use_container_width=True)
        
        # 2. Enhanced Word Frequency Analysis
        st.subheader("Common Red Flag Terms")
        
        # Extract and visualize common concerning terms
        all_text = " ".join(df[description_column].astype(str)).lower()
        red_flag_terms = [
            term for term in re.findall(r'\b\w{4,}\b', all_text) 
            if term in [
                "payment", "deposit", "fee", "unpaid", 
                "required", "money", "investment", 
                "registration", "training", "guaranteed"
            ]
        ]
        
        if red_flag_terms:
            term_counts = pd.Series(red_flag_terms).value_counts().reset_index()
            term_counts.columns = ["Term", "Count"]
            
            fig4 = px.bar(
                term_counts,
                x="Term",
                y="Count",
                color="Count",
                color_continuous_scale="Reds",
                title="Frequency of Red Flag Terms",
                labels={'Count': 'Occurrences', 'Term': ''},
                height=400
            )
            fig4.update_layout(
                xaxis={'categoryorder':'total descending'},
                coloraxis_showscale=False
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.success("No common red flag terms detected in descriptions")

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
