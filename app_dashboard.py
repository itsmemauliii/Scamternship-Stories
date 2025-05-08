pip install pdfplumber streamlit pandas plotly wordcloud matplotlib
import streamlit as st
import pandas as pd
import plotly.express as px
import pdfplumber
from scam_analysis import check_scam_risk
import io
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Scamternship Detector Dashboard", layout="wide")
st.title("🚩 Scamternship Detector Dashboard")
st.markdown("""
Analyze internship/job descriptions to identify potential scams, red flags, and suspicious patterns. 
This tool is part of the #ScamternshipStories initiative by Tech Data Hub.
""")

# Custom CSS for better visuals
st.markdown("""
<style>
    .red-flag { color: #ff4b4b; font-weight: bold; }
    .safe-flag { color: #0068c9; font-weight: bold; }
    .header-font { font-size:18px !important; }
</style>
""", unsafe_allow_html=True)

# File Upload
uploaded_file = st.file_uploader("Upload a PDF or CSV file with Job Descriptions", 
                                type=["pdf", "csv"])

def extract_text_from_pdf(pdf_file):
    all_text = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)
    return "\n".join(all_text)

def analyze_text(text):
    # Split by potential job description markers (customize as needed)
    descriptions = [jd.strip() for jd in re.split(r'\n\d+\.|\n•|\n-', text) if jd.strip()]
    return descriptions

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        # Process PDF
        with st.spinner("Extracting text from PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
            descriptions = analyze_text(pdf_text)
            df = pd.DataFrame({"Job Description": descriptions})
    else:
        # Process CSV
        df = pd.read_csv(uploaded_file)
        jd_column = st.selectbox("Select the column containing job descriptions:", df.columns)
        descriptions = df[jd_column].tolist()

    # Analysis
    with st.spinner("Analyzing job descriptions for scam patterns..."):
        results = []
        for jd in descriptions:
            if pd.notnull(jd) and str(jd).strip():
                output = check_scam_risk(str(jd))
                results.append(output)
            else:
                results.append({"score": 0, "flags": [], "advice": "No description provided."})

        df["Scam Score"] = [r["score"] for r in results]
        df["Red Flags"] = [", ".join(r["flags"]) for r in results]
        df["Advice"] = [r["advice"] for r in results]
        df["Risk Level"] = pd.cut(df["Scam Score"], 
                                 bins=[-1, 20, 40, 60, 100],
                                 labels=["Low", "Moderate", "High", "Very High"])

    st.success("Analysis complete!")
    
    # Main Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Listings", len(df))
    with col2:
        risky = len(df[df["Scam Score"] >= 40])
        st.metric("Potentially Risky", f"{risky} ({risky/len(df)*100:.1f}%)")
    with col3:
        avg_score = df["Scam Score"].mean()
        st.metric("Average Scam Score", f"{avg_score:.1f}/100")

    # Data Display
    st.subheader("🔍 Analysis Results")
    st.dataframe(df.style.applymap(lambda x: 'color: red' if isinstance(x, str) and 'High risk' in x else '', 
                subset=["Advice"]))

    # Visualizations
    st.subheader("📊 Scam Analysis Dashboard")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Score Distribution", "Risk Levels", "Red Flag Cloud", "Detailed Analysis"])
    
    with tab1:
        fig = px.histogram(df, x="Scam Score", nbins=20, 
                          color_discrete_sequence=['#ff6b6b'],
                          title="Distribution of Scam Scores")
        fig.update_layout(xaxis_title="Scam Score", yaxis_title="Number of Listings")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        risk_counts = df["Risk Level"].value_counts().reset_index()
        fig = px.pie(risk_counts, values='count', names='Risk Level',
                    color='Risk Level',
                    color_discrete_map={'Low':'#2ecc71',
                                       'Moderate':'#f39c12',
                                       'High':'#e74c3c',
                                       'Very High':'#c0392b'},
                    hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### 🚩 Most Common Red Flags")
        all_flags = " ".join([flag for sublist in df["Red Flags"] for flag in sublist.split(", ") if flag])
        if all_flags:
            wordcloud = WordCloud(width=800, height=400, 
                                background_color='white',
                                colormap='Reds',
                                max_words=50).generate(all_flags)
            fig, ax = plt.subplots()
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
        else:
            st.info("No red flags detected in these listings.")
    
    with tab4:
        st.markdown("### 📈 Detailed Risk Analysis")
        fig = px.box(df, y="Scam Score", points="all",
                    hover_data=["Job Description"],
                    title="Detailed Scam Score Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 🏆 Top 5 Safest Listings")
        safest = df.nsmallest(5, "Scam Score")[["Job Description", "Scam Score"]]
        st.table(safest)
        
        st.markdown("### 🚨 Top 5 Riskiest Listings")
        riskiest = df.nlargest(5, "Scam Score")[["Job Description", "Scam Score", "Red Flags"]]
        st.table(riskiest)

    # Download
    st.subheader("🧾 Download Results")
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Analysis')
        workbook = writer.book
        worksheet = writer.sheets['Analysis']
        
        # Add some formatting
        format_red = workbook.add_format({'bg_color': '#ffcccc'})
        worksheet.conditional_format('D2:D1000', {'type': 'cell',
                                                'criteria': '>=',
                                                'value': 40,
                                                'format': format_red})
    
    st.download_button(
        label="Download Full Report (Excel)",
        data=output.getvalue(),
        file_name="scamternship_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Please upload a PDF or CSV file to begin analysis.")
    st.image("https://via.placeholder.com/800x400?text=Upload+a+PDF+or+CSV+with+Job+Descriptions", 
             use_column_width=True)
