window.addEventListener("DOMContentLoaded", (loadEvent) => {
    document.querySelector("main").addEventListener("click", (ev) => {
        const el = ev.target;
        const main = el.closest("main");

        if (main.classList.contains("tekir_contents")) {
            const deleteDialog = document.getElementById("delete-confirm");
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
            }
        }

        if (main.classList.contains("tekir_content_edit")) {
            const details = el.closest("details");
            if (details) {  // flowblock-related event
                ev.preventDefault();
            }
            const saveDialog = document.getElementById("save-dialog");
            const changesDialog = document.getElementById("changes-dialog");
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
                details.remove();
            } else if (el.classList.contains("up-block")) {
                details.previousElementSibling.before(details);
            } else if (el.classList.contains("down-block")) {
                details.nextElementSibling.after(details);
            }
            }
    });

    document.body.addEventListener("showChanges", (ev) => {
        document.getElementById("changes-dialog").showModal();
        document.getElementById("changes-continue").setAttribute("data-href", ev.detail.href);
    });
});
