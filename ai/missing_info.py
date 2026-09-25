def detect_missing_information(text):
    """
    Detects common missing information from a document.
    """

    if not text:
        return []

    text_lower = text.lower()

    checks = [
        ("Purpose", ["purpose", "objective", "goal"]),
        ("Timeline", ["timeline", "deadline", "date", "schedule"]),
        ("Budget", ["budget", "cost", "price", "amount"]),
        ("Contact Information", ["contact", "email", "phone"]),
        ("Location", ["location", "address", "place"]),
        ("Expected Outcome", ["outcome", "result", "expected"]),
    ]

    missing_information = []

    for item, keywords in checks:

        found = any(
            keyword in text_lower
            for keyword in keywords
        )

        if not found:
            missing_information.append(item)

    return missing_information