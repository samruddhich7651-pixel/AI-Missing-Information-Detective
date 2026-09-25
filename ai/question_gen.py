def generate_questions(missing_information):
    """
    Generates investigation questions
    from detected missing information.
    """

    if not missing_information:
        return []

    question_templates = {
        "Purpose": "What is the main purpose or objective of this document?",
        "Timeline": "What is the expected timeline or deadline?",
        "Budget": "What is the estimated budget or total cost?",
        "Contact Information": "Who is the responsible person or contact?",
        "Location": "Where will the activity or project take place?",
        "Expected Outcome": "What result or outcome is expected?"
    }

    questions = []

    for item in missing_information:

        question = question_templates.get(
            item,
            f"What information is missing about {item}?"
        )

        questions.append(question)

    return questions