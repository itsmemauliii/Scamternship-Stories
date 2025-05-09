import openai
import os

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")  # Or set directly for testing

def analyze_with_genai(description):
    prompt = f"""
You are a career advisor and scam detector. Analyze the following job description and:
1. Tell whether it's a scam or not.
2. List any red flags.
3. Provide short advice to the job seeker.

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

        result = response.choices[0].message.content.strip()
        return result

    except Exception as e:
        return f"Error: {e}"
