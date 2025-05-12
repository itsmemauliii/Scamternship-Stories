import re

def check_scam_risk(description):
    """
    Analyzes a job description for potential scam indicators.

    Args:
        description (str): The job description to analyze.

    Returns:
        dict: A dictionary containing the scam risk score, identified red flags, and advice.
    """
    red_flags = []
    score = 0

    # Define patterns for different scam indicators
    patterns = {
        "Unpaid Opportunity": r"\bunpaid\b|\bno (?:stipend|payment|compensation)\b|\bwithout pay\b",
        "Advance Fee Scam": r"(?:pay|deposit|transfer|fee).*?(?:application|registration|process|confirm|fee|amount|INR|₹|\d+)\b",
        "Guaranteed Job Scam": r"\bguarantee.*?\bjob\b|\bjob.*?\bguarantee\b",
        "Certificate Scam": r"\bonly certificate\b|\bcertificate after payment\b|\bpay.*?certificate\b",
        "No Proper Documentation": r"\bno offer letter\b|\bverbal confirmation\b|\bafter payment.*?letter\b",
        "Too Good to Be True": r"\bno experience needed\b|\bno interview required\b|\bimmediate joining\b|\bwork from top MNC\b",
        "High Pressure Tactics": r"\blimited time\b|\bimmediate\b|\bhurry\b|\bselected\b.*?\bpay\b",
        "Suspicious Payment Amounts": r"\b\d{4,}\b.*?(?:fee|deposit|pay)"
    }

    # Check each pattern against the description
    for flag, pattern in patterns.items():
        if re.search(pattern, description, re.IGNORECASE):
            red_flags.append(flag)
            # Assign different weights for different flags
            if flag in ["Advance Fee Scam", "Guaranteed Job Scam"]:
                score += 30
            elif flag in ["Too Good to Be True", "High Pressure Tactics"]:
                score += 25
            else:
                score += 20

    # Additional checks for amounts mentioned with payment requests
    payment_amounts = re.findall(r"(?:pay|deposit|fee).*?(\d{4,})", description, re.IGNORECASE)
    if payment_amounts and "Advance Fee Scam" not in red_flags:
        red_flags.append("Advance Fee Scam")
        score += 30

    # Determine advice based on the score
    if score >= 60:
        advice = "High risk: Very likely a scam - avoid completely."
    elif score >= 40:
        advice = "Significant risk: Probably a scam - strongly consider avoiding."
    elif score >= 20:
        advice = "Moderate risk: Possible scam - exercise extreme caution."
    else:
        advice = "Low risk: Seems legitimate but still verify details."

    return {"score": score, "flags": red_flags, "advice": advice}

# Sample usage
if __name__ == "__main__":
    # Example job descriptions to analyze
    descriptions = [
        "This is an unpaid internship with no experience needed. Hurry, apply now!",
        "We guarantee you a job after a small training fee. No interviews required!",
        "This opportunity offers a certificate after payment. Apply today!",
        "Seeking a motivated intern to assist with marketing tasks. This is an unpaid internship offering valuable experience."
    ]

    for desc in descriptions:
        result = check_scam_risk(desc)
        print(f"Description: {desc}\nResult: {result}\n")
