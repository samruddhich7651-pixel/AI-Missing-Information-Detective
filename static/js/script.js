document.addEventListener("DOMContentLoaded", function () {

    // ==============================
    // PAGE LOADING
    // ==============================

    document.body.classList.add("page-loaded");


    // ==============================
    // FILE NAME DISPLAY
    // ==============================

    const fileInput = document.querySelector("#document_file");
    const fileName = document.querySelector(".upload-file-name");

    if (fileInput && fileName) {

        fileInput.addEventListener("change", function () {

            if (this.files.length > 0) {
                fileName.textContent = this.files[0].name;
            } else {
                fileName.textContent = "No file selected";
            }

        });

    }


    // ==============================
    // IMAGE NAME DISPLAY
    // ==============================

    const imageInput = document.querySelector("#image_file");
    const imageName = document.querySelector(".image-file-name");

    if (imageInput && imageName) {

        imageInput.addEventListener("change", function () {

            if (this.files.length > 0) {
                imageName.textContent = this.files[0].name;
            } else {
                imageName.textContent = "No image selected";
            }

        });

    }


    // ==============================
    // SCORE PROGRESS BARS
    // ==============================

    const progressBars =
        document.querySelectorAll(".progress-fill");

    progressBars.forEach(function (bar) {

        const score = bar.dataset.score || 0;

        setTimeout(function () {
            bar.style.width = score + "%";
        }, 150);

    });


    // ==============================
    // ANALYSIS FORM VALIDATION
    // ==============================

    const analysisForm =
        document.querySelector(
            'form[action="/generate_roadmap"]'
        );

    if (analysisForm) {

        analysisForm.addEventListener(
            "submit",
            function (event) {

                const fileInput =
                    document.querySelector("#document_file");

                const imageInput =
                    document.querySelector("#image_file");

                const textArea =
                    document.querySelector(
                        'textarea[name="document_text"]'
                    );

                const urlInput =
                    document.querySelector(
                        'input[name="document_url"]'
                    );


                const hasFile =
                    fileInput &&
                    fileInput.files.length > 0;

                const hasImage =
                    imageInput &&
                    imageInput.files.length > 0;

                const hasText =
                    textArea &&
                    textArea.value.trim().length > 0;

                const hasURL =
                    urlInput &&
                    urlInput.value.trim().length > 0;


                // At least ONE input is required
                if (
                    !hasFile &&
                    !hasImage &&
                    !hasText &&
                    !hasURL
                ) {

                    event.preventDefault();

                    alert(
                        "Please provide a file, image, text, or URL."
                    );

                }

            }
        );

    }

});