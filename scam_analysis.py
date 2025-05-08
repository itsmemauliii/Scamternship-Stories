
import re

def check_scam_risk(description):
    red_flags = []
    score = 0

    patterns = {
        "Unpaid": r"unpaid|no stipend|zero compensation",
        "Advance Fee": r"(pay|deposit|transfer).*?(registration|fee|amount|INR|₹)",
        "No Offer Letter": r"no offer letter|verbal confirmation only",
        "Certificate Scam": r"only certificate|certificate after payment",
        "No Learning": r"no training|no guidance|self learning"
    }

    for flag, pattern in patterns.items():
        if re.search(pattern, description, re.IGNORECASE):
            red_flags.append(flag)
            score += 20

    advice = "Consider avoiding this opportunity." if score >= 40 else "Exercise caution and verify legitimacy."
    return {"score": score, "flags": red_flags, "advice": advice}
