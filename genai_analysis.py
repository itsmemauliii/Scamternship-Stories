import openai
import streamlit as st
import os

def analyze_with_genai(text, api_key):
    """
    Analyzes text using OpenAI's GPT model for potential scam indicators.
    Now accepts the API key as an argument.
    """
    try:
        if not api_key:
            st.warning("OpenAI API key is not provided to the analysis function.")
            return "API key not provided"

        openai.api_key = api_key  # Set the API key within the function's scope
        response = openai.ChatCompletion.create(
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
    
    # For direct testing, you'd still need to provide an API key
    test_api_key = os.environ.get("OPENAI_API_KEY")
    if test_api_key:
        analysis_result = analyze_with_genai(test_text, test_api_key)
        print(f"Analysis of: '{test_text}'\nResult: {analysis_result}")
    else:
        print("Please set the OPENAI_API_KEY environment variable for direct testing.")

    test_text_no_scam = "Seeking a motivated intern to assist with marketing tasks. This is an unpaid internship offering valuable experience."
    if test_api_key:
        analysis_result_no_scam = analyze_with_genai(test_text_no_scam, test_api_key)
        print(f"Analysis of: '{test_text_no_scam}'\nResult: {analysis_result_no_scam}")
