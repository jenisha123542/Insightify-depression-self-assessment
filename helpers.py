def get_result_details(score):
    if score <= 4:
        result = "Minimal or no depression"
        message = "Your responses suggest little to no signs of depression."
        recommendations = [
            "Continue healthy routines like regular sleep and exercise.",
            "Stay connected with friends and family.",
            "Practice mindfulness or journaling.",
            "No clinical intervention is necessary, but remain self-aware."
        ]
        doctors = []  # Add doctors based on severity if applicable
    elif score <= 9:
        result = "Mild depression"
        message = "You may be experiencing mild symptoms of depression."
        recommendations = [
            "Try mood-boosting activities (e.g., walking, music, sunlight).",
            "Practice stress management (meditation, yoga).",
            "Talk to a trusted person or counselor.",
            "Monitor your mood over the next few weeks."
        ]
        doctors = []  # Add doctors based on severity if applicable
    elif score <= 14:
        result = "Moderate depression"
        message = "Your results indicate a moderate level of depression."
        recommendations = [
            "Consider talking to a mental health professional.",
            "Cognitive Behavioral Therapy (CBT) can be very helpful.",
            "Start journaling and tracking mood/sleep/diet.",
            "Engage in positive social interactions."
        ]
        doctors = ["Dr. John Doe (Psychiatrist)", "Dr. Jane Smith (Psychologist)"]
    elif score <= 19:
        result = "Moderately severe depression"
        message = "Your results suggest moderately severe depression symptoms."
        recommendations = [
            "It’s strongly recommended to consult a licensed therapist or counselor.",
            "Psychological therapy (CBT, IPT) or medication may be needed.",
            "Avoid alcohol or substance use.",
            "Create a daily self-care and activity plan."
        ]
        doctors = ["Dr. Emily White (Therapist)", "Dr. Michael Black (Psychiatrist)"]
    else:
        result = "Severe depression"
        message = "Your results indicate severe symptoms of depression."
        recommendations = [
            "Seek immediate support from a mental health professional.",
            "Therapy + medication is usually most effective at this stage.",
            "Inform a trusted family member or friend.",
            "Crisis helplines or emergency services may be necessary if you're in danger."
        ]
        doctors = ["Dr. Susan Green (Psychiatrist)", "Dr. Robert Brown (Therapist)"]

    return result, message, recommendations, doctors
