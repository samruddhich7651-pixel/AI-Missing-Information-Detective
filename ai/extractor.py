def extract_text_from_text(text):
    """
    Cleans and prepares document text for analysis.
    """

    if not text:
        return ""

    cleaned_text = text.strip()

    # Remove unnecessary blank lines
    lines = [
        line.strip()
        for line in cleaned_text.splitlines()
        if line.strip()
    ]

    return "\n".join(lines)