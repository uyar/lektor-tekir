window.addEventListener("DOMContentLoaded", (loadEvent) => {
    const uiLang = localStorage.getItem("ui-language");
    const pageLang = document.documentElement.getAttribute("lang");
    if (uiLang && (uiLang != pageLang)) {
        window.location.href = window.location.href.replace("/" + pageLang + "/", "/" + uiLang + "/");
    }

    document.querySelectorAll("#tekir-langs a").forEach((el) => {
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
            if (ev.currentTarget.classList.contains("light")) {
                document.documentElement.setAttribute("color-mode", "light");
                localStorage.setItem("color-mode", "light");
            } else {
                document.documentElement.setAttribute("color-mode", "dark");
                localStorage.setItem("color-mode", "dark");
            }
        });
    });

    document.querySelector("main").addEventListener("click", (ev) => {
        const el = ev.target;
        const main = el.closest("main");

        if (main.classList.contains("tekir_summary")) {
            const publishDialog = document.getElementById("publish-select");
            if (el.id == "tekir-publish") {
                publishDialog.showModal();
            } else if (el.id == "publish-cancel") {
                ev.preventDefault();
                publishDialog.close();
            }
        } else if (main.classList.contains("tekir_contents")) {
            const deleteDialog = document.getElementById("delete-confirm");
            const addSubpageDialog = document.getElementById("add-subpage-form");
            const addAttachmentDialog = document.getElementById("add-attachment-form");
            if (el.classList.contains("delete-content")) {
                document.getElementById("delete-continue").setAttribute("hx-include", "#" + el.closest("form").id);
                deleteDialog.showModal();
            } else if (el.id == "delete-continue") {
                const formId = el.getAttribute("hx-include");
                document.querySelector(formId).querySelectorAll("input:checked").forEach((checkbox) => {
                    checkbox.closest("tr").remove();
                });
                deleteDialog.close();
            } else if (el.id == "delete-cancel") {
                deleteDialog.close();
            } else if (el.id == "add-subpage") {
                ev.preventDefault();
                document.querySelector("#add-subpage-form form").reset();
                document.getElementById("add-subpage-result").innerHTML = "";
                addSubpageDialog.showModal();
            } else if (el.id == "add-subpage-confirm") {
                if (document.getElementById("add-subpage-result").innerHTML == "OK") {
                    addSubpageDialog.close();
                }
            } else if (el.id == "add-subpage-cancel") {
                ev.preventDefault();
                addSubpageDialog.close();
            } else if (el.id == "add-attachment") {
                ev.preventDefault();
                document.querySelector("#add-attachment-form form").reset();
                document.getElementById("add-attachment-result").innerHTML = "";
                addAttachmentDialog.showModal();
            } else if (el.id == "add-attachment-confirm") {
                if (document.getElementById("add-attachment-result").innerHTML == "OK") {
                    addAttachmentDialog.close();
                }
            } else if (el.id == "add-attachment-cancel") {
                ev.preventDefault();
                addAttachmentDialog.close();
            }
        } else if (main.classList.contains("tekir_content_edit")) {
            const details = el.closest("details");
            const saveDialog = document.getElementById("save-dialog");
            const changesDialog = document.getElementById("changes-dialog");
            const navigateDialog = document.getElementById("navigate-dialog");
            if (el.id == "save-content") {
                saveDialog.showModal();
            } else if (el.id == "save-close") {
                saveDialog.close();
            } else if (el.id == "changes-continue") {
                changesDialog.close();
                window.location.href = el.dataset.href;
            } else if (el.id == "changes-cancel") {
                changesDialog.close();
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
                navigateDialog. showModal();
            } else if (el.id == "navigate-select") {
                document.getElementById(el.dataset.src).value = document.getElementById("navigables").value;
                navigateDialog.close();
            } else if (el.id == "navigate-cancel") {
                navigateDialog.close();
            }
        } else if (main.classList.contains("tekir_attachment_edit")) {
            const replaceAttachmentDialog = document.getElementById("replace-attachment-form");
            if (el.id == "replace-attachment") {
                ev.preventDefault();
                document.querySelector("#replace-attachment-form form").reset();
                document.getElementById("replace-attachment-result").innerHTML = "";
                replaceAttachmentDialog.showModal();
            } else if (el.id == "replace-attachment-confirm") {
                if (document.getElementById("replace-attachment-result").innerHTML == "OK") {
                    replaceAttachmentDialog.close();
                }
            } else if (el.id == "replace-attachment-cancel") {
                ev.preventDefault();
                replaceAttachmentDialog.close();
            }
        }
    });

    document.body.addEventListener("showChanges", (ev) => {
        document.getElementById("changes-dialog").showModal();
        document.getElementById("changes-continue").setAttribute("data-href", ev.detail.href);
    });

    document.body.addEventListener("updateSlug", (ev) => {
        document.getElementById("field-slug").setAttribute("placeholder", ev.detail.slug);
    });
});
