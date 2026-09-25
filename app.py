from flask import Flask, render_template, request, redirect, url_for, session

from database.database import (
    init_database,
    save_analysis,
    get_all_analyses,
    get_analysis_by_id
)

from ai.analyzer import analyze_document

from pypdf import PdfReader
from docx import Document

import requests
from bs4 import BeautifulSoup

from urllib.parse import urljoin
from io import BytesIO

import re


app = Flask(__name__)

app.secret_key = "missing_information_detective_secret"

init_database()


# =========================================================
# FILE TEXT EXTRACTION
# =========================================================

def extract_text_from_file(uploaded_file):

    filename = uploaded_file.filename.lower()

    # TXT
    if filename.endswith(".txt"):

        return uploaded_file.read().decode(
            "utf-8",
            errors="ignore"
        )

    # PDF
    if filename.endswith(".pdf"):

        pdf_data = uploaded_file.read()

        reader = PdfReader(
            BytesIO(pdf_data)
        )

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text

    # DOCX
    if filename.endswith(".docx"):

        document = Document(uploaded_file)

        text = ""

        for paragraph in document.paragraphs:

            text += paragraph.text + "\n"

        return text

    return ""


# =========================================================
# PDF TEXT EXTRACTION FROM BYTES
# =========================================================

def extract_text_from_pdf_bytes(pdf_bytes):

    reader = PdfReader(
        BytesIO(pdf_bytes)
    )

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text.strip()


# =========================================================
# URL TEXT + PDF EXTRACTION
# =========================================================

def extract_text_from_url(url):

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        }
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    # DIRECT PDF URL

    if (
        "application/pdf" in content_type
        or url.lower().split("?")[0].endswith(".pdf")
    ):

        text = extract_text_from_pdf_bytes(
            response.content
        )

        print(
            "DIRECT PDF TEXT LENGTH:",
            len(text)
        )

        return (
            text,
            response.content,
            "application/pdf"
        )

    # WEBPAGE / FLIPLINK PAGE

    page_html = response.text

    soup = BeautifulSoup(
        page_html,
        "html.parser"
    )

    # FIND PDF URL

    pdf_url = None

    pdf_matches = re.findall(
        r"""['"]([^'"]+\.pdf(?:\?[^'"]*)?)['"]""",
        page_html,
        re.IGNORECASE
    )

    if pdf_matches:

        pdf_path = pdf_matches[0]

        pdf_url = urljoin(
            url,
            pdf_path
        )

    # FLIPLINK PdfURL VARIABLE

    if not pdf_url:

        pdf_variable_match = re.search(
            r"""PdfURL\s*=\s*['"]([^'"]+)['"]""",
            page_html,
            re.IGNORECASE
        )

        if pdf_variable_match:

            pdf_path = pdf_variable_match.group(1)

            pdf_url = urljoin(
                url,
                pdf_path
            )

    # OTHER PDF VARIABLE PATTERNS

    if not pdf_url:

        pdf_variable_match = re.search(
            r"""(?:pdf|downloadURL|downloadUrl)\s*[:=]\s*['"]([^'"]+\.pdf[^'"]*)['"]""",
            page_html,
            re.IGNORECASE
        )

        if pdf_variable_match:

            pdf_path = pdf_variable_match.group(1)

            pdf_url = urljoin(
                url,
                pdf_path
            )

    # DOWNLOAD PDF

    if pdf_url:

        print(
            "FOUND PDF URL:",
            pdf_url
        )

        pdf_response = requests.get(
            pdf_url,
            timeout=30,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                ),
                "Referer": url
            }
        )

        pdf_response.raise_for_status()

        pdf_bytes = pdf_response.content

        pdf_text = extract_text_from_pdf_bytes(
            pdf_bytes
        )

        print(
            "PDF TEXT LENGTH:",
            len(pdf_text)
        )

        return (
            pdf_text,
            pdf_bytes,
            "application/pdf"
        )

    # FALLBACK: NORMAL WEBPAGE TEXT

    for element in soup([
        "script",
        "style",
        "noscript",
        "header",
        "footer",
        "nav"
    ]):

        element.decompose()

    text = soup.get_text(
        separator=" ",
        strip=True
    )

    print(
        "WEBPAGE TEXT LENGTH:",
        len(text)
    )

    return text, None, None


# =========================================================
# MAIN PAGES
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


@app.route("/upload")
def upload():

    return render_template(
        "upload.html"
    )


@app.route("/analysis")
def analysis():

    return render_template(
        "analysis.html"
    )


@app.route("/results")
def results():

    analysis_data = session.get(
        "analysis"
    )

    document_name = session.get(
        "document_name",
        "Document"
    )

    return render_template(
        "results.html",
        analysis=analysis_data,
        document_name=document_name
    )


@app.route("/questions")
def questions():

    analysis_data = session.get(
        "analysis"
    )

    return render_template(
        "questions.html",
        analysis=analysis_data
    )


@app.route("/score")
def score():

    analysis_data = session.get(
        "analysis"
    )

    return render_template(
        "score.html",
        analysis=analysis_data
    )


@app.route("/history")
def history():

    try:

        analyses = get_all_analyses()

        return render_template(
            "history.html",
            analyses=analyses
        )

    except Exception as e:

        print(
            "HISTORY ERROR:",
            repr(e)
        )

        return render_template(
            "history.html",
            analyses=[]
        )


@app.route("/admin")
def admin():

    try:

        analyses = get_all_analyses()

        return render_template(
            "admin.html",
            analyses=analyses
        )

    except Exception as e:

        print(
            "ADMIN ERROR:",
            repr(e)
        )

        return render_template(
            "admin.html",
            analyses=[]
        )


# =========================================================
# VIEW OLD HISTORY ANALYSIS
# =========================================================

@app.route("/history/<int:analysis_id>")
def view_history_analysis(analysis_id):

    try:

        saved_analysis = get_analysis_by_id(
            analysis_id
        )

        if not saved_analysis:

            return redirect(
                url_for("history")
            )

        analysis_data = {}

        if saved_analysis["analysis_result"]:

            try:

                import json

                analysis_data = json.loads(
                    saved_analysis["analysis_result"]
                )

            except Exception as e:

                print(
                    "HISTORY JSON ERROR:",
                    repr(e)
                )

                analysis_data = {}

        session["analysis"] = analysis_data

        session["document_name"] = (
            saved_analysis["document_name"]
        )

        return redirect(
            url_for("results")
        )

    except Exception as e:

        print(
            "VIEW HISTORY ERROR:",
            repr(e)
        )

        return redirect(
            url_for("history")
        )


# =========================================================
# DOCUMENT ANALYSIS
# =========================================================

@app.route(
    "/generate_roadmap",
    methods=["POST"]
)
def generate_analysis():

    document_name = request.form.get(
        "document_name",
        ""
    ).strip()

    document_text = request.form.get(
        "document_text",
        ""
    ).strip()

    document_url = request.form.get(
        "document_url",
        ""
    ).strip()

    uploaded_file = request.files.get(
        "document"
    )

    allowed_extensions = (
        ".pdf",
        ".docx",
        ".txt",
        ".jpg",
        ".jpeg",
        ".png"
    )

    image_bytes = None
    image_mime = None


    # =====================================================
    # URL INPUT
    # =====================================================

    if document_url:

        print(
            "URL RECEIVED:",
            document_url
        )

        try:

            (
                document_text,
                url_file_bytes,
                url_file_mime
            ) = extract_text_from_url(
                document_url
            )

            document_name = document_url

            if url_file_bytes:

                image_bytes = url_file_bytes

                image_mime = url_file_mime

            print(
                "FINAL URL TEXT LENGTH:",
                len(document_text)
            )

            print(
                "URL FILE MIME:",
                image_mime
            )

        except Exception as e:

            print(
                "URL ERROR:",
                repr(e)
            )

            return redirect(
                url_for("upload")
            )


    # =====================================================
    # FILE INPUT
    # =====================================================

    elif (
        uploaded_file
        and uploaded_file.filename
    ):

        filename = (
            uploaded_file.filename.lower()
        )

        if not filename.endswith(
            allowed_extensions
        ):

            print(
                "INVALID FILE EXTENSION:",
                filename
            )

            return redirect(
                url_for("upload")
            )

        document_name = (
            uploaded_file.filename
        )

        try:

            # IMAGE

            if filename.endswith(
                (".jpg", ".jpeg", ".png")
            ):

                image_bytes = (
                    uploaded_file.read()
                )

                if filename.endswith(
                    (".jpg", ".jpeg")
                ):

                    image_mime = "image/jpeg"

                else:

                    image_mime = "image/png"


            # PDF / DOCX / TXT

            else:

                extracted_text = (
                    extract_text_from_file(
                        uploaded_file
                    )
                )

                if extracted_text.strip():

                    document_text = (
                        extracted_text.strip()
                    )

        except Exception as e:

            print(
                "FILE ERROR:",
                repr(e)
            )

            return redirect(
                url_for("upload")
            )


    # =====================================================
    # EMPTY INPUT CHECK
    # =====================================================

    if (
        not document_text
        and not image_bytes
    ):

        print(
            "EMPTY DOCUMENT TEXT"
        )

        print(
            "DOCUMENT URL:",
            document_url
        )

        print(
            "DOCUMENT NAME:",
            document_name
        )

        return redirect(
            url_for("upload")
        )


    # =====================================================
    # AI ANALYSIS
    # =====================================================

    print(
        "STARTING AI ANALYSIS..."
    )

    try:

        analysis_result = analyze_document(
            document_text,
            image_bytes=image_bytes,
            image_mime=image_mime
        )

        print(
            "AI ANALYSIS COMPLETED"
        )

    except Exception as e:

        print(
            "AI ANALYSIS ERROR:",
            repr(e)
        )

        return redirect(
            url_for("upload")
        )


    # =====================================================
    # CHECK AI RESULT
    # =====================================================

    if not isinstance(
        analysis_result,
        dict
    ):

        print(
            "INVALID AI RESULT"
        )

        return redirect(
            url_for("upload")
        )


    # =====================================================
    # SAVE SESSION
    # =====================================================

    session["analysis"] = (
        analysis_result
    )

    session["document_name"] = (
        document_name
        if document_name
        else "Untitled Investigation"
    )


    # =====================================================
    # SAVE HISTORY
    # =====================================================

    try:

        save_analysis(
            session["document_name"],
            document_text,
            analysis_result.get(
                "completeness_score",
                0
            ),
            analysis_result
        )

        print(
            "ANALYSIS SAVED TO HISTORY"
        )

    except Exception as e:

        print(
            "DATABASE SAVE ERROR:",
            repr(e)
        )


    # =====================================================
    # SHOW RESULTS
    # =====================================================

    return redirect(
        url_for("results")
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return redirect(
        url_for("home")
    )


@app.errorhandler(500)
def internal_server_error(error):

    print(
        "SERVER ERROR:",
        repr(error)
    )

    return redirect(
        url_for("upload")
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )