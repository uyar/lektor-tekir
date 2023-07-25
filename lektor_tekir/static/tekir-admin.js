window.addEventListener("DOMContentLoaded", (loadEvent) => {
    const uiLang = localStorage.getItem("ui-language");
    const pageLang = document.documentElement.getAttribute("lang");
    if (uiLang && (uiLang != pageLang)) {
        window.location.href = window.location.href.replace("/" + pageLang + "/", "/" + uiLang + "/");
    }

    document.querySelectorAll("#tekir-langs a.button").forEach((el) => {
        el.addEventListener("click", (ev) => {
            localStorage.setItem("ui-language", ev.currentTarget.innerHTML);
        });
    });

    const colorMode = localStorage.getItem("color-mode");
    if (colorMode) {
        document.documentElement.setAttribute("color-mode", colorMode);
    }

    document.querySelectorAll("button.color-mode").forEach((el) => {
        el.addEventListener("click", (ev) => {
            const mode = ev.currentTarget.dataset.mode;
            document.documentElement.setAttribute("color-mode", mode);
            localStorage.setItem("color-mode", mode);
        });
    });

    document.querySelector("main").addEventListener("click", (ev) => {
        const el = ev.target.closest("button") ?? ev.target;
        const main = el.closest("main");

        if (el.classList.contains("modal-close")) {
            ev.preventDefault();
            el.closest("dialog").close();
        } else if (el.classList.contains("add-content")) {
            ev.preventDefault();
            const form = document.getElementById(el.dataset.formid);
            form.reset();
            form.querySelector(".warning").innerHTML = "";
            form.closest("dialog").showModal();
    } else if (main.classList.contains("tekir_overview")) {
            if (el.id == "publish-button") {
                document.getElementById("publish-dialog").showModal();
            }
        } else if (main.classList.contains("tekir_contents")) {
            const deleteDialog = document.getElementById("delete-dialog");
            if (el.classList.contains("delete-content")) {
                document.getElementById("delete-continue").setAttribute("hx-include", "#" + el.closest("form").id);
                deleteDialog.showModal();
            } else if (el.id == "delete-continue") {
                const formId = el.getAttribute("hx-include");
                document.querySelector(formId).querySelectorAll("input:checked").forEach((checkbox) => {
                    checkbox.closest("tr").remove();
                });
                deleteDialog.close();
            }
        } else if (main.classList.contains("tekir_content_edit")) {
            const details = el.closest("details");
            const navigateDialog = document.getElementById("navigate-dialog");
            if (el.id == "save-content") {
                document.getElementById("save-dialog").showModal();
            } else if (el.id == "changes-continue") {
                document.getElementById("changes-dialog").close();
                window.location.href = el.dataset.href;
            } else if (el.classList.contains("delete-block")) {
                ev.preventDefault();
                details.remove();
            } else if (el.classList.contains("up-block")) {
                ev.preventDefault();
                details.previousElementSibling.before(details);
            } else if (el.classList.contains("down-block")) {
                ev.preventDefault();
                details.nextElementSibling.after(details);
            } else if (el.classList.contains("tekir-navigate")) {
                document.getElementById("navigate-select").setAttribute("data-src", el.id);
                navigateDialog.showModal();
            } else if (el.id == "navigate-select") {
                ev.preventDefault();
                document.getElementById(el.dataset.src).value = document.getElementById("navigables").value;
                navigateDialog.close();
            }
        }
    });

    document.body.addEventListener("showChanges", (ev) => {
        document.getElementById("changes-continue").setAttribute("data-href", ev.detail.href);
        document.getElementById("changes-dialog").showModal();
    });

    document.body.addEventListener("updateSlug", (ev) => {
        document.getElementById("field-slug").setAttribute("placeholder", ev.detail.slug);
    });
});
