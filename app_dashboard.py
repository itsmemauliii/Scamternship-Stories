import streamlit as st
import pandas as pd
import plotly.express as px
from scam_analysis import check_scam_risk
import io
import re
pip install pdfplumber wordcloud matplotlib

# Check for all optional dependencies
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from wordcloud import WordCloud
    WORDCLOUD_SUPPORT = True
except ImportError:
    WORDCLOUD_SUPPORT = False

if not WORDCLOUD_SUPPORT:
    st.warning("Word cloud disabled - install with: `pip install wordcloud`")

pip install --upgrade streamlit

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_SUPPORT = True
except ImportError:
    MATPLOTLIB_SUPPORT = False

st.set_page_config(page_title="Scamternship Detector Dashboard", layout="wide")
st.title("🚩 Scamternship Detector Dashboard")

def generate_wordcloud(text):
    """Generate word cloud with fallback if dependencies not available"""
    if not WORDCLOUD_SUPPORT or not MATPLOTLIB_SUPPORT:
        return None
    
    try:
        wordcloud = WordCloud(width=800, height=400, 
                            background_color='white',
                            colormap='Reds',
                            max_words=50).generate(text)
        fig, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        return fig
    except Exception as e:
        st.error(f"Word cloud generation failed: {str(e)}")
        return None

# Initialize tabs
tab1, tab2, tab3 = st.tabs(["Data Upload", "Analysis Results", "Red Flags Word Cloud"])

# Sample data - replace with your actual data loading logic
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        'Job Title': ['Marketing Intern', 'Data Analyst', 'Remote Assistant'],
        'Company': ['ABC Corp', 'XYZ Inc', 'Home Based Jobs'],
        'Red Flags': ['No payment, Unclear requirements', 
                     'No contract, Vague description',
                     'Request personal information']
    })

df = st.session_state.df

with tab1:
    st.header("Upload Your Data")
    uploaded_file = st.file_uploader(
        "Choose a file (CSV, PDF, or text)",
        type=['csv', 'pdf', 'txt'],
        accept_multiple_files=False,
        help="Upload internship listings for analysis (max 200MB)"
    )
    
    if uploaded_file:
        st.success(f"File {uploaded_file.name} uploaded successfully!")

with tab2:
    st.header("Analysis Results")
    if not df.empty:
        # Apply scam analysis if check_scam_risk function exists
        if 'check_scam_risk' in globals():
            try:
                df['Risk Score'] = df['Red Flags'].apply(lambda x: check_scam_risk(str(x)))
                st.dataframe(df.sort_values('Risk Score', ascending=False))
                
                # Visualize risk scores if available
                if 'Risk Score' in df.columns:
                    fig = px.bar(df, x='Job Title', y='Risk Score', color='Company',
                                title='Scam Risk by Internship Position')
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Analysis error: {str(e)}")
                st.dataframe(df)
        else:
            st.dataframe(df)
    else:
        st.info("No data available. Please upload a file in the Data Upload tab.")

with tab3:  # Word Cloud tab
    st.markdown("### 🚩 Most Common Red Flags")
    
    # Safely extract flags
    try:
        if not df.empty and 'Red Flags' in df.columns:
            all_flags = " ".join([flag for sublist in df["Red Flags"] 
                                for flag in str(sublist).split(", ") if flag])
        else:
            all_flags = ""
    except Exception as e:
        st.error(f"Error processing flags: {str(e)}")
        all_flags = ""
    
    if all_flags.strip():
        if WORDCLOUD_SUPPORT and MATPLOTLIB_SUPPORT:
            wc_fig = generate_wordcloud(all_flags)
            if wc_fig:
                st.pyplot(wc_fig)
            else:
                # Fallback to text display
                top_flags = ", ".join(sorted(set(all_flags.split()))[:10])
                st.info(f"Top flags: {top_flags}")
        else:
            # Fallback to text display
            top_flags = ", ".join(sorted(set(all_flags.split()))[:10])
            st.info(f"Top flags: {top_flags}")
    else:
        st.info("No red flags detected in these listings.")
