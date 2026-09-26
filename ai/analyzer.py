import os
import json
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing. Please add it to .env"
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# JSON CLEANING
# =========================================================

def clean_json_response(text):

    if not text:
        return ""

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    # Remove control characters
    text = "".join(
        char
        for char in text
        if ord(char) >= 32
        or char in "\n\r\t"
    )

    # Find first JSON object
    start = text.find("{")

    if start != -1:
        end = text.rfind("}")

        if end != -1:
            text = text[start:end + 1]

    return text.strip()


def repair_json_text(text):

    if not text:
        return text

    # Remove trailing commas
    text = re.sub(
        r",\s*([}\]])",
        r"\1",
        text
    )

    # Remove unusual characters that sometimes appear
    # immediately before JSON closing brackets.
    text = re.sub(
        r"[\u0000-\u001F\u007F-\u009F]+(?=\s*[\]\}])",
        "",
        text
    )

    return text.strip()


# =========================================================
# DEFAULT RESULT
# =========================================================

def default_result():

    return {
        "missing_information": [],
        "unclear_information": [],
        "contradictions": [],
        "evidence": [],
        "questions": [],
        "completeness_score": 0,
        "priority": {
            "critical": [],
            "important": [],
            "optional": []
        }
    }


# =========================================================
# VALIDATE AI RESULT
# =========================================================

def validate_result(result):

    if not isinstance(result, dict):
        return default_result()

    required_list_fields = [
        "missing_information",
        "unclear_information",
        "contradictions",
        "evidence",
        "questions"
    ]

    for field in required_list_fields:

        if field not in result:
            result[field] = []

        if not isinstance(result[field], list):
            result[field] = []


    # Priority
    if not isinstance(
        result.get("priority"),
        dict
    ):
        result["priority"] = {
            "critical": [],
            "important": [],
            "optional": []
        }


    for priority_name in [
        "critical",
        "important",
        "optional"
    ]:

        if priority_name not in result["priority"]:
            result["priority"][priority_name] = []

        if not isinstance(
            result["priority"][priority_name],
            list
        ):
            result["priority"][priority_name] = []


    # Score
    score = result.get(
        "completeness_score",
        0
    )

    try:

        if isinstance(score, str):

            match = re.search(
                r"\d+(?:\.\d+)?",
                score
            )

            if match:
                score = float(match.group())
            else:
                score = 0

        score = float(score)

    except Exception:

        score = 0


    score = max(
        0,
        min(
            100,
            score
        )
    )


    if score.is_integer():
        score = int(score)


    result["completeness_score"] = score


    return result


# =========================================================
# ANALYZE DOCUMENT
# =========================================================

def analyze_document(
    document_text,
    image_bytes=None,
    image_mime=None
):

    print(
        "========================================"
    )

    print(
        "STARTING DOCUMENT ANALYSIS"
    )

    print(
        "TEXT LENGTH:",
        len(document_text or "")
    )

    print(
        "IMAGE PROVIDED:",
        bool(image_bytes)
    )

    print(
        "IMAGE MIME:",
        image_mime
    )

    print(
        "========================================"
    )


    # =====================================================
    # CLEAN INPUT
    # =====================================================

    document_text = (
        document_text or ""
    ).strip()


    # If absolutely nothing was provided
    if not document_text and not image_bytes:

        print(
            "NO DOCUMENT CONTENT PROVIDED"
        )

        return default_result()


    # =====================================================
    # AI PROMPT
    # =====================================================

    prompt = """
You are an expert document investigation AI.

Your job is to analyze the supplied document and identify:

1. Missing information
2. Unclear or ambiguous information
3. Contradictions
4. Important evidence already present
5. Useful questions the user should ask
6. Overall completeness score

IMPORTANT:

- Analyze ONLY information relevant to the document's actual purpose.
- First understand what type of document it is.
- Do NOT assume every standard field must exist.
- Do NOT mark optional information as missing.
- Do NOT invent information.
- Do NOT create weak or generic findings.
- Prefer fewer accurate findings over many false positives.

For resumes:

- Do NOT automatically mark LinkedIn, GitHub, GPA/CGPA,
  certifications, internships, achievements, extracurriculars,
  leadership, hobbies or references as missing.
- Only flag them if they are clearly required for the stated
  purpose or explicitly expected by the document context.
- Future dates alone are NOT contradictions.
- Short project descriptions are NOT automatically unclear.

For certificates and official documents:

- Focus on information that is genuinely necessary for
  identification, verification, validity or intended use.
- Do not invent requirements that are not relevant to the document.

For contracts, offers and agreements:

- Focus on important terms, obligations, dates, payment,
  duration, location, notice periods, conditions and rights
  when those details are relevant to the document purpose.

For general documents:

- Identify meaningful information gaps that could affect
  understanding, verification or decision making.

COMPLETENESS SCORE:

The score must be an integer from 0 to 100.

100 means the document contains essentially all important
information needed for its purpose.

0 means the document contains almost no useful information
for its purpose.

The score must be based on the actual document content.

Do NOT return 0 simply because some optional information
is missing.

QUALITY CHECK:

Before returning the final JSON:

- Remove duplicate findings.
- Remove weak findings.
- Remove optional information that is not genuinely needed.
- Do not treat future dates as contradictions unless two
  pieces of information actually conflict.
- Make sure every missing or unclear item has a useful reason.
- Make sure the score matches the actual findings.

RETURN ONLY VALID JSON.

The JSON must have exactly this structure:

{
  "missing_information": [
    {
      "item": "string",
      "priority": "critical|important|optional",
      "details": "string"
    }
  ],
  "unclear_information": [
    {
      "item": "string",
      "priority": "critical|important|optional",
      "details": "string"
    }
  ],
  "contradictions": [
    {
      "item": "string",
      "priority": "critical|important|optional",
      "details": "string"
    }
  ],
  "evidence": [
    "string"
  ],
  "questions": [
    "string"
  ],
  "completeness_score": 0,
  "priority": {
    "critical": [],
    "important": [],
    "optional": []
  }
}

Do not add markdown.
Do not add explanations outside JSON.
"""


    # =====================================================
    # ADD TEXT TO PROMPT
    # =====================================================

    if document_text:

        prompt += """

DOCUMENT CONTENT:

---------------- DOCUMENT START ----------------

""" + document_text + """

----------------- DOCUMENT END -----------------

Analyze the document content above.
"""


    # =====================================================
    # PREPARE GEMINI CONTENT
    # =====================================================

    contents = []


    # Text prompt
    contents.append(
        prompt
    )


    # =====================================================
    # IMAGE CONTENT
    # =====================================================

    if image_bytes:

        print(
            "ADDING IMAGE TO GEMINI REQUEST"
        )

        try:

            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=(
                    image_mime
                    or "image/png"
                )
            )

            contents.append(
                image_part
            )

        except Exception as e:

            print(
                "IMAGE PART ERROR:",
                repr(e)
            )

            return default_result()


    # =====================================================
    # GEMINI CALL
    # =====================================================

    print(
        "CALLING GEMINI..."
    )

    try:

        response = client.models.generate_content(

            model="gemini-2.5-flash",

            contents=contents,

            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )


    except Exception as e:

        print(
            "GEMINI API ERROR:",
            repr(e)
        )

        return default_result()


    print(
        "GEMINI RESPONSE RECEIVED"
    )


    # =====================================================
    # RAW RESPONSE
    # =====================================================

    raw_response = ""

    try:

        raw_response = (
            response.text
            or ""
        )

    except Exception:

        raw_response = ""


    print(
        "RAW AI RESPONSE:"
    )

    print(
        raw_response
    )


    # =====================================================
    # EMPTY RESPONSE
    # =====================================================

    if not raw_response.strip():

        print(
            "EMPTY GEMINI RESPONSE"
        )

        return default_result()


    # =====================================================
    # CLEAN JSON
    # =====================================================

    cleaned_json = clean_json_response(
        raw_response
    )

    cleaned_json = repair_json_text(
        cleaned_json
    )


    # =====================================================
    # PARSE JSON
    # =====================================================

    result = None


    try:

        result = json.loads(
            cleaned_json
        )

    except Exception as first_error:

        print(
            "FIRST JSON PARSE ERROR:",
            repr(first_error)
        )


        # Second repair attempt
        try:

            repaired = repair_json_text(
                cleaned_json
            )

            result = json.loads(
                repaired
            )

        except Exception as second_error:

            print(
                "SECOND JSON PARSE ERROR:",
                repr(second_error)
            )

            print(
                "CLEANED JSON:"
            )

            print(
                cleaned_json
            )

            return default_result()


    # =====================================================
    # VALIDATE RESULT
    # =====================================================

    result = validate_result(
        result
    )


    # =====================================================
    # FINAL LOGS
    # =====================================================

    print(
        "AI RESULT:",
        result
    )

    print(
        "AI SCORE:",
        result.get(
            "completeness_score",
            0
        )
    )

    print(
        "RAW SCORE VALUE:",
        result.get(
            "completeness_score"
        ),
        "TYPE:",
        type(
            result.get(
                "completeness_score"
            )
        ).__name__
    )

    print(
        "FINAL AI SCORE:",
        result.get(
            "completeness_score",
            0
        )
    )

    print(
        "========================================"
    )

    return result