window.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("button.color-mode").forEach(btn => {
        btn.addEventListener("click", (e) => {
            if (e.currentTarget.classList.contains("light")) {
                document.documentElement.setAttribute("color-mode", "light");
            } else {
                document.documentElement.setAttribute("color-mode", "dark");
            }
        });
    });
});
