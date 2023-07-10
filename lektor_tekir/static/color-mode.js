window.addEventListener("DOMContentLoaded", () => {
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
});
