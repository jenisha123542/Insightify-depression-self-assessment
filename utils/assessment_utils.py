def map_assessment_to_risk(assessment):
    assessment = assessment.lower()
    if "minimal" in assessment or "no depression" in assessment:
        return "low", "Minimal Risk", "You appear to have minimal symptoms of depression. Stay positive!"
    elif "mild" in assessment:
        return "moderate", "Mild to Moderate Risk", "You may be experiencing mild symptoms of depression. Consider speaking with a counselor."
    elif "moderate" in assessment or "moderately severe" in assessment:
        return "moderate", "Moderate Risk", "You may be experiencing noticeable symptoms of depression. A consultation with a mental health expert is recommended."
    elif "severe" in assessment:
        return "high", "High Risk", "You may be experiencing severe depression. Please consult a licensed mental health professional immediately."
    else:
        return "low", "Unknown", "We couldn't interpret the result. Please retake the test or contact support."
