window.addEventListener("DOMContentLoaded", (loadEvent) => {
    const uiLang = localStorage.getItem("ui-language");
    const pageLang = document.documentElement.getAttribute("lang");
    if (uiLang && (uiLang != pageLang)) {
        window.location.href = window.location.href.replace("/" + pageLang + "/", "/" + uiLang + "/");
    }

    document.querySelectorAll("#language-panel a.button").forEach((el) => {
        el.addEventListener("click", (ev) => {
            localStorage.setItem("ui-language", ev.currentTarget.innerHTML);
        });
    });

    document.querySelector("main").addEventListener("click", (ev) => {
        const el = ev.target.closest("button") ?? ev.target;
        const main = el.closest("main");

        if (el.classList.contains("modal-close")) {
            ev.preventDefault();
            el.closest("dialog").close();
        } else if (main.classList.contains("tekir_content_edit")) {
            const details = el.closest("details");
            if (el.classList.contains("delete-block")) {
                ev.preventDefault();
                details.remove();
            } else if (el.classList.contains("up-block")) {
                ev.preventDefault();
                details.previousElementSibling.before(details);
            } else if (el.classList.contains("down-block")) {
                ev.preventDefault();
                details.nextElementSibling.after(details);
            } else if (el.id == "navigate-select") {
                ev.preventDefault();
                document.getElementById(el.dataset.dst).value = document.getElementById("navigables").value;
                el.closest("dialog").close();
            }
        }
    });

    document.body.addEventListener("updateAttr", (ev) => {
        document.querySelector(ev.detail.target).setAttribute(ev.detail.attr, ev.detail.value);
    });

    document.body.addEventListener("showModal", (ev) => {
        document.querySelector(ev.detail.modal).showModal();
    });

    document.body.addEventListener("deleteCheckedRows", (ev) => {
        document.querySelector(ev.detail.form).querySelectorAll("input:checked").forEach((checkbox) => {
            checkbox.closest("tr").remove();
        });
        document.querySelector(ev.detail.modal).close();
    });
});
