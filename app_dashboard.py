import streamlit as st
import pandas as pd
import plotly.express as px
from scam_analysis import check_scam_risk
import io
import re

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

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_SUPPORT = True
except ImportError:
    MATPLOTLIB_SUPPORT = False

st.set_page_config(page_title="Scamternship Detector Dashboard", layout="wide")
st.title("🚩 Scamternship Detector Dashboard")

# Warning messages for missing dependencies
if not PDF_SUPPORT:
    st.warning("PDF processing disabled - install with: `pip install pdfplumber`")
if not WORDCLOUD_SUPPORT:
    st.warning("Word cloud disabled - install with: `pip install wordcloud`")
if not MATPLOTLIB_SUPPORT:
    st.warning("Matplotlib disabled - install with: `pip install matplotlib`")

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

# [Rest of your existing code...]

with tab3:  # Word Cloud tab
    st.markdown("### 🚩 Most Common Red Flags")
    
    # Safely extract flags
    try:
        all_flags = " ".join([flag for sublist in df["Red Flags"] 
                            for flag in str(sublist).split(", ") if flag])
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
