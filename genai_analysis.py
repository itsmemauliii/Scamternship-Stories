# genai_analysis.py
import openai
import streamlit as st

# Use Streamlit secrets for API key (set in secrets.toml or Streamlit Cloud)
openai.api_key = st.secrets.get("OPENAI_API_KEY")

def analyze_with_genai(description):
    prompt = f"""
You are an expert scam detector and career advisor. Analyze the following job description and:
1. Say whether it's likely a scam or not.
2. List any red flags you identify.
3. Give a brief piece of advice to the applicant.

Job Description:
\"\"\"
{description}
\"\"\"
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"[GENAI ERROR] {str(e)}"
