import streamlit as st
import pandas as pd
import plotly.express as px
from scam_analysis import check_scam_risk
import io
import re
import matplotlib.pyplot as plt
import numpy as np

# Check for optional dependencies
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

st.set_page_config(page_title="Scamternship Detector Dashboard", layout="wide")
st.title("🚩 Scamternship Detector Dashboard")

# Warning messages for missing dependencies
if not PDF_SUPPORT:
    st.warning("PDF processing disabled - install with: `pip install pdfplumber`")
if not WORDCLOUD_SUPPORT:
    st.warning("Word cloud disabled - install with: `pip install wordcloud`")

def generate_wordcloud(text):
    """Generate word cloud with fallback if not available"""
    if not WORDCLOUD_SUPPORT:
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

# [Rest of your existing code for file upload and processing...]

# Modified visualization section with fallbacks
with tab3:  # Word Cloud tab
    st.markdown("### 🚩 Most Common Red Flags")
    all_flags = " ".join([flag for sublist in df["Red Flags"] for flag in sublist.split(", ") if flag])
    
    if all_flags:
        if WORDCLOUD_SUPPORT:
            wc_fig = generate_wordcloud(all_flags)
            if wc_fig:
                st.pyplot(wc_fig)
            else:
                st.info("Couldn't generate word cloud")
        else:
            st.info("Top flags: " + ", ".join(sorted(set(all_flags.split()))[:10])
    else:
        st.info("No red flags detected in these listings.")
