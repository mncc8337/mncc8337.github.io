import * as cookie from "./cookie.js";

// colorscheme button
let colorscheme = cookie.getCookie("colorscheme");
if(colorscheme == "") {
    colorscheme = "light";
}
let colorschemeButton = document.getElementById("colorscheme-button");
if(colorscheme == "light") {
    colorschemeButton.innerHTML= "🔥";
} else {
    colorschemeButton.innerHTML= "🦉";
}
function toggleColorscheme() {
    if(colorscheme == "light") {
        colorscheme = "dark";
        colorschemeButton.innerHTML= "🦉";
    } else {
        colorscheme = "light";
        colorschemeButton.innerHTML= "🔥";
    }

    cookie.setCookie("colorscheme", colorscheme, "SameSite=Lax; path=/");
    document.documentElement.style.setProperty("color-scheme", colorscheme);
}
document.getElementById("colorscheme-button").addEventListener("click", toggleColorscheme);

// back-to-top button
const bttButton = document.getElementById("back-to-top");
window.addEventListener("scroll", () => {
    if(window.scrollY > 800) {
        bttButton.classList.add("show");
    } else {
        bttButton.classList.remove("show");
    }
});
bttButton.addEventListener("click", () => {
    window.scrollTo({
        top: 0,
        behavior: "smooth",
    });
});
