window.addEventListener("DOMContentLoaded", (ev) => {
    const deleteDialog = document.getElementById("delete-confirm");

    document.querySelectorAll(".delete-content").forEach((el) => {
        el.addEventListener("click", (ev) => {
            document.getElementById("delete-continue").setAttribute("hx-include", "#" + el.closest("form").id);
            deleteDialog.showModal();
        });
    });

    document.getElementById("delete-continue").addEventListener("click", (evt) => {
        evt.preventDefault();
        const formId = evt.target.getAttribute("hx-include");
        document.querySelector(formId).querySelectorAll("input:checked").forEach((el) => {
            el.closest("tr").remove();
        });
        deleteDialog.close();
    });

    document.getElementById("delete-cancel").addEventListener("click", (evt) => {
        evt.preventDefault();
        deleteDialog.close();
    });
});
