import * as cookie from "./cookie.js";

function updateYear() {
    let elements = document.getElementsByClassName("current-year");

    for(let i = 0; i < elements.length; i++) {
        let element = elements[i];
        element.innerHTML = new Date().getFullYear();
    }
}

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

// make functions accessible to html
window.toggleColorscheme = toggleColorscheme

window.onload = function() {
    // update footer year
    updateYear();

    // load colorscheme
    setColorscheme(getColorscheme());
}

