import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re
#import subprocess #not used
#import sys #not used
#import os #not used

# **IMPORTANT: `st.set_page_config()` MUST be the very first Streamlit call.**
st.set_page_config(page_title="Scamternship Detector Dashboard", layout="wide")

# Import wordcloud and matplotlib at the top, but conditionally use them.
try:
    import wordcloud
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# Define check_scam_risk. It's good practice to define functions before using them.
def check_scam_risk(text):
    """
    Checks for scam indicators in the given text.

    Args:
        text (str): The text to analyze.

    Returns:
        int: A risk score (higher is riskier).
    """
    risk_score = 0
    text = text.lower()  # Ensure case-insensitive matching

    # Define red flag keywords/phrases. Use a list for easier extension.
    red_flags = [
        "no payment",
        "unpaid internship",
        "unclear requirements",
        "vague description",
        "no contract",
        "request personal information",
        "immediate start",
        "work from home only",
        "guaranteed placement",
        "high pay, little work",
        "urgent hiring",
        "investment required",
        "sponsor fee",
        "recruitment fee",
        "training fee",
    ]

    # Check for red flags
    for flag in red_flags:
        if flag in text:
            risk_score += 1

    # Additional checks (more complex patterns)
    if re.search(r"\b(wire|transfer)\s+money\b", text):
        risk_score += 2
    if re.search(r"(ssn|social security number)", text):
        risk_score += 2
    if re.search(r"interview\s+via\s+(text|chat|telegram|whatsapp)", text):
        risk_score += 1

    return risk_score



# Initialize tabs
tab1, tab2, tab3 = st.tabs(
    ["Data Upload", "Analysis Results", "Red Flags Word Cloud"]
)

# Sample data - replace with your actual data loading logic
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(
        {
            "Job Title": [
                "Marketing Intern",
                "Data Analyst",
                "Remote Assistant",
                "Software Engineer",
            ],
            "Company": [
                "ABC Corp",
                "XYZ Inc",
                "Home Based Jobs",
                "Tech Innovators",
            ],
            "Red Flags": [
                "No payment, Unclear requirements",
                "No contract, Vague description",
                "Request personal information",
                "Unpaid Internship, High pay, little work",
            ],
        }
    )

df = st.session_state.df


def load_data(uploaded_file):
    """Loads data from the uploaded file, handling different file types."""
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            return df
        elif uploaded_file.name.endswith(".txt"):
            text_content = uploaded_file.read().decode("utf-8")
            # Basic parsing: split by lines, assume comma-separated within lines.
            lines = text_content.strip().split("\n")
            data = [line.split(",") for line in lines]
            # Create DataFrame, handling potential header row
            if data:
                header = data[0]
                if (
                    len(header) > 1
                ):  # check if the first row can be header
                    try:
                        df = pd.DataFrame(data[1:], columns=header)
                        return df
                    except ValueError:
                        df = pd.DataFrame(data)
                        df.columns = [f"Column_{i}" for i in range(len(df.columns))]
                        return df
                else:
                    df = pd.DataFrame(data)
                    df.columns = [f"Column_{i}" for i in range(len(df.columns))]
                    return df
            else:
                return pd.DataFrame()  # Return empty DataFrame
        elif uploaded_file.name.endswith(".pdf"):
            import pdfplumber
            text_content = ""
            try:
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        text_content += page.extract_text() + " "
            except Exception as e:
                st.error(f"Error reading PDF: {e}")
                return pd.DataFrame()
            # Very basic parsing of PDF text. This will need improvement.
            lines = text_content.strip().split("\n")
            data = [line.split(",") for line in lines]
            # Create DataFrame, handling potential header row
            if data:
                header = data[0]
                if (
                    len(header) > 1
                ):  # check if the first row can be header
                    try:
                        df = pd.DataFrame(data[1:], columns=header)
                        return df
                    except ValueError:
                        df = pd.DataFrame(data)
                        df.columns = [f"Column_{i}" for i in range(len(df.columns))]
                        return df
                else:
                    df = pd.DataFrame(data)
                    df.columns = [f"Column_{i}" for i in range(len(df.columns))]
                    return df
            else:
                return pd.DataFrame()  # Return empty DataFrame
        else:
            st.error("Unsupported file type. Please upload a CSV, TXT, or PDF file.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()



with tab1:
    st.header("Upload Your Data")
    uploaded_file = st.file_uploader(
        "Choose a file (CSV, PDF, or text)",
        type=["csv", "pdf", "txt"],
        accept_multiple_files=False,
        help="Upload internship listings for analysis (max 200MB)",
    )

    if uploaded_file:
        st.success(f"File {uploaded_file.name} uploaded successfully!")
        df = load_data(uploaded_file)  # Load data.
        st.session_state.df = df  # store the dataframe
        if not df.empty:  # show the first 5 rows
            st.write("First 5 rows of uploaded data:")
            st.dataframe(df.head())


with tab2:
    st.header("Analysis Results")
    # Access the dataframe from the session state
    df = st.session_state.df
    if not df.empty:
        # Apply scam analysis
        if "check_scam_risk" in globals():
            try:
                # Ensure 'Red Flags' column exists
                if "Red Flags" not in df.columns:
                    df["Red Flags"] = (
                        "No flags"  # Or some default value
                    )
                    st.warning(
                        "The 'Red Flags' column was not found in your data. Analysis will be based on other columns."
                    )

                df["Risk Score"] = df["Red Flags"].apply(
                    lambda x: check_scam_risk(str(x))
                )
                st.dataframe(df.sort_values("Risk Score", ascending=False))

                # Visualize risk scores
                if "Risk Score" in df.columns:
                    fig = px.bar(
                        df,
                        x="Job Title",
                        y="Risk Score",
                        color="Company",
                        title="Scam Risk by Internship Position",
                    )
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
        df = st.session_state.df  # get the dataframe
        if not df.empty and "Red Flags" in df.columns:
            all_flags = " ".join(
                [
                    flag
                    for sublist in df["Red Flags"]
                    for flag in str(sublist).split(", ")
                    if flag
                ]
            )
        else:
            all_flags = ""
    except Exception as e:
        st.error(f"Error processing flags: {str(e)}")
        all_flags = ""

    if all_flags.strip():
        if WORDCLOUD_AVAILABLE and MATPLOTLIB_AVAILABLE:
            wc_fig = generate_wordcloud(all_flags)
            if wc_fig:
                st.pyplot(wc_fig)
            else:
                # Fallback to text display
                unique_flags = list(
                    set(filter(None, all_flags.split()))
                )  # remove empty strings
                if len(unique_flags) > 10:
                    top_flags = ", ".join(sorted(unique_flags)[:10])
                else:
                    top_flags = ", ".join(sorted(unique_flags))
                st.info(f"Top flags: {top_flags}")
        else:
            unique_flags = list(
                set(filter(None, all_flags.split()))
            )  # remove empty strings
            if len(unique_flags) > 10:
                top_flags = ", ".join(sorted(unique_flags)[:10])
            else:
                top_flags = ", ".join(sorted(unique_flags))
            st.info(f"Top flags: {top_flags}")
    else:
        st.info("No red flags detected in these listings.")
