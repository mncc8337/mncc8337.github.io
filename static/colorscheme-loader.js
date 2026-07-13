let theme = "light";
if(document.cookie.includes("colorscheme=dark")) {
    theme = "dark";
}
document.documentElement.style.setProperty("color-scheme", theme);
