import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


def analyze_document(text, image_bytes=None, image_mime=None):

    prompt = """
You are an expert AI Missing Information Detective.

Your job is to deeply analyze the provided document or image and identify
what information is present, missing, unclear, contradictory, and what
questions should be asked before making an informed decision.

IMPORTANT ANALYSIS PROCESS:

1. FIRST understand the document and identify its type and purpose.
2. Extract the important facts actually present.
3. Identify information that is genuinely missing and would reasonably
   be expected for this type of document.
4. Identify vague, incomplete, ambiguous or confusing statements.
5. Identify contradictions only when two pieces of information actually
   conflict with each other.
6. Identify important evidence/facts that support the analysis.
7. Generate practical questions directly related to the detected gaps.
8. Assign realistic priority levels.
9. Calculate a meaningful completeness score from 0 to 100.

IMAGE RULES:

- If an image is provided, carefully read all visible text.
- Extract information from the image before deciding what is missing.
- Do NOT say information is missing if it is clearly visible in the image.
- Consider headings, tables, dates, numbers, names and other visible details.
- Do not assume an image contains no useful information.

IMPORTANT:

- Do not invent facts.
- Do not assume information that is not present.
- Do not create contradictions without actual conflicting information.
- Do not mark normal optional details as missing unless they are relevant
  to the purpose of the document.
- Analyze the document according to its actual context and purpose.

DOCUMENT-TYPE AWARE ANALYSIS:

Adapt the analysis to the document type.

For example:

- Job offer:
  salary, role, location, working hours, joining date, notice period,
  probation, bond, benefits and other relevant employment terms.

- Contract/agreement:
  parties, obligations, payment, duration, termination, penalties,
  responsibilities and important conditions.

- Resume:
  contact information, education, skills, experience, dates,
  achievements and other important professional information.

- Invoice:
  seller, buyer, invoice number, date, items, quantities, prices,
  taxes, totals and payment information.

- Academic document:
  institution, subject/course, dates, marks/grades, requirements
  and other relevant academic details.

- General document:
  identify its purpose first and then determine what information
  is reasonably necessary for understanding or decision-making.

MISSING INFORMATION:

Only include information that is genuinely absent and important
for understanding, verification or decision-making.

UNCLEAR INFORMATION:

Include statements that are vague, ambiguous, incomplete or could
reasonably have multiple interpretations.

CONTRADICTIONS:

Only report a contradiction when two pieces of information in the
document directly conflict.

EVIDENCE:

Include important facts, figures, dates, names, statements or clues
that are actually present in the document and support the analysis.

QUESTIONS:

Every question should be practical and connected to a detected
missing or unclear item.

PRIORITY:

Classify important missing and unclear items into:

critical:
Essential information that could significantly affect money,
legal obligations, safety, deadlines, major decisions or outcomes.

important:
Useful information that should normally be clarified before
making a proper decision, but is not immediately critical.

optional:
Helpful additional information that improves understanding but
is not necessary for the main decision.

Priority rules:

- Use only detected missing or unclear items.
- Do not invent priority items.
- Put each item in only ONE priority category.
- Do not mark everything as critical.
- Contradictions can be treated as critical or important when
  they materially affect the document's meaning.
- Keep priority classification consistent with the actual document.

COMPLETENESS SCORE:

Calculate an integer from 0 to 100.

The score represents how complete and decision-ready the document is.

Consider:

- Important information that is present.
- Important information that is missing.
- Unclear information.
- Contradictions.
- The purpose and type of the document.

Guidelines:

90-100 = very complete, little important information missing.
75-89 = mostly complete, some useful information missing.
50-74 = several important gaps or unclear details.
25-49 = major information is missing or unclear.
0-24 = very incomplete or unreliable for decision-making.

Do not automatically give a high score just because the document
contains a lot of text.

Return ONLY valid JSON.

Use exactly this structure:

{
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
"""

    if text:
        prompt += "\n\nDOCUMENT TEXT:\n" + text

    try:

        contents = []

        if image_bytes and image_mime:

            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=image_mime
            )

            contents.append(image_part)

        contents.append(prompt)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        result_text = response.text.strip()

        if result_text.startswith("```"):

            result_text = result_text.replace(
                "```json",
                ""
            )

            result_text = result_text.replace(
                "```",
                ""
            )

            result_text = result_text.strip()

        result = json.loads(result_text)

        # ---------------------------------------------
        # REQUIRED FIELDS
        # ---------------------------------------------

        required_fields = [
            "missing_information",
            "unclear_information",
            "contradictions",
            "evidence",
            "questions",
            "completeness_score",
            "priority"
        ]

        for field in required_fields:

            if field not in result:

                if field == "completeness_score":

                    result[field] = 0

                elif field == "priority":

                    result[field] = {
                        "critical": [],
                        "important": [],
                        "optional": []
                    }

                else:

                    result[field] = []

        # ---------------------------------------------
        # ENSURE LIST FIELDS ARE LISTS
        # ---------------------------------------------

        list_fields = [
            "missing_information",
            "unclear_information",
            "contradictions",
            "evidence",
            "questions"
        ]

        for field in list_fields:

            if not isinstance(result[field], list):

                result[field] = []

        # ---------------------------------------------
        # PRIORITY VALIDATION
        # ---------------------------------------------

        if not isinstance(
            result["priority"],
            dict
        ):

            result["priority"] = {
                "critical": [],
                "important": [],
                "optional": []
            }

        for priority_level in [
            "critical",
            "important",
            "optional"
        ]:

            if (
                priority_level
                not in result["priority"]
                or not isinstance(
                    result["priority"][priority_level],
                    list
                )
            ):

                result["priority"][priority_level] = []

        # ---------------------------------------------
        # SCORE VALIDATION
        # ---------------------------------------------

        try:

            score = int(
                result["completeness_score"]
            )

        except (TypeError, ValueError):

            score = 0

        score = max(
            0,
            min(100, score)
        )

        result["completeness_score"] = score

        return result

    except Exception as e:

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
            },
            "error": str(e)
        }