window.addEventListener("DOMContentLoaded", () => {
    const colorMode = localStorage.getItem("color-mode");
    console.log(colorMode);
    if (colorMode) {
        document.documentElement.setAttribute("color-mode", colorMode);
    }

    document.querySelectorAll("button.color-mode").forEach(btn => {
        btn.addEventListener("click", (e) => {
            if (e.currentTarget.classList.contains("light")) {
                document.documentElement.setAttribute("color-mode", "light");
                localStorage.setItem("color-mode", "light");
            } else {
                document.documentElement.setAttribute("color-mode", "dark");
                localStorage.setItem("color-mode", "dark");
            }
        });
    });
});
