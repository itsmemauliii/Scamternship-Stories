# genai_analysis.py
import openai
import streamlit as st
import os

def analyze_with_genai(text, api_key):
    """
    Analyzes text using OpenAI's GPT model for potential scam indicators.
    Accepts the API key as an argument.
    """
    try:
        openai.api_key = api_key
        if not openai.api_key:
            st.warning("API key was not provided to the analysis function.")
            return "API key not provided"

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Or another suitable model
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

if __name__ == '__main__':
    print("Running genai_analysis.py directly (for testing):")
    test_text = "This amazing opportunity guarantees you a high-paying role immediately after you pay a small training fee. No experience needed!"
    # When running directly, it won't have Streamlit secrets
    analysis_result = analyze_with_genai(test_text, os.environ.get("OPENAI_API_KEY"))
    print(f"Analysis of: '{test_text}'\nResult: {analysis_result}")

    test_text_no_scam = "Seeking a motivated intern to assist with marketing tasks. This is an unpaid internship offering valuable experience."
    analysis_result_no_scam = analyze_with_genai(test_text_no_scam, os.environ.get("OPENAI_API_KEY"))
    print(f"Analysis of: '{test_text_no_scam}'\nResult: {analysis_result_no_scam}")
