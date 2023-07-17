window.addEventListener("DOMContentLoaded", (loadEvent) => {
    document.querySelector("main").addEventListener("click", (ev) => {
        const el = ev.target;
        const main = el.closest("main");

        if (main.classList.contains("tekir_contents")) {
            const deleteDialog = document.getElementById("delete-confirm");
            const addSubpageDialog = document.getElementById("add-form");
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
                addSubpageDialog.showModal();
            } else if (el.id == "add-confirm") {
                addSubpageDialog.close();
            } else if (el.id == "add-cancel") {
                ev.preventDefault();
                addSubpageDialog.close();
            }
        }

        if (main.classList.contains("tekir_content_edit")) {
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
