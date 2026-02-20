import * as cookie from "./cookie.js";

function getColorscheme() {
    let saved_colorscheme = cookie.getCookie("colorscheme");
    if(saved_colorscheme != "") {
        return saved_colorscheme;
    } else {
        return "light";
    }
}

function setColorscheme(colorscheme) {
    let button = document.getElementById("colorscheme-button");
    if(colorscheme == "light") {
        button.innerHTML= "🔥";
    } else {
        button.innerHTML= "🦉";
    }

    cookie.setCookie("colorscheme", colorscheme, "SameSite=Lax; path=/");
    document.documentElement.style.setProperty("color-scheme", colorscheme);
}


function toggleColorscheme() {
    let colorscheme = getColorscheme();

    if(colorscheme == "light") {
        colorscheme = "dark";
    } else {
        colorscheme = "light";
    }

    setColorscheme(colorscheme);
}

// load colorscheme on page load
setColorscheme(getColorscheme());

//initialise back-to-top button
const bttButton = document.getElementById("back-to-top");
window.addEventListener("scroll", () => {
    if(window.scrollY > 800) {
        bttButton.classList.add("show");
    } else {
        bttButton.classList.remove("show");
    }
});

// attach buttons' event
document.getElementById("colorscheme-button").addEventListener("click", toggleColorscheme);
bttButton.addEventListener("click", () => {
    window.scrollTo({
        top: 0,
        behavior: "smooth",
    });
});
