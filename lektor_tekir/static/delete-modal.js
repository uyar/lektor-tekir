window.addEventListener("DOMContentLoaded", (e) => {
    const deleteDialog = document.getElementById("delete-confirm");

    document.querySelectorAll(".delete-content").forEach((el) => {
        el.addEventListener("click", () => {
            document.getElementById("delete-item-type").innerHTML = el.dataset.type;
            document.getElementById("delete-item-path").innerHTML = el.dataset.path;
            document.getElementById("delete-continue").setAttribute(
              "hx-vals",
              "js:{'path': document.getElementById('delete-item-path').innerHTML}"
            );
            deleteDialog.showModal();
        });
    });

    document.getElementById("delete-continue").addEventListener("click", () => {
        const deletedItemPath = document.getElementById('delete-item-path').innerHTML;
        const deletedButton = document.querySelector("button[data-path='" + deletedItemPath + "']");
        const deletedRow = deletedButton.closest("tr");
        deletedRow.remove();
        deleteDialog.close();
    });

    document.getElementById("delete-cancel").addEventListener("click", () => {
        deleteDialog.close();
    });
});
