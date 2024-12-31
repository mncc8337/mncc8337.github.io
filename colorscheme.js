var colorscheme = null;
var button = null;

function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');

    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while(c.charAt(0) == ' ')
            c = c.substring(1);

        if(c.indexOf(name) == 0)
            return c.substring(name.length, c.length);
    }

    return "";
}

function setColorscheme() {
    if(colorscheme == "light") {
        button.innerHTML= "🔥";
    } else {
        button.innerHTML= "🦉";
    }

    document.cookie = "colorscheme=" + colorscheme + "; SameSite=Lax; path=/";
    document.documentElement.style.setProperty("color-scheme", colorscheme);
}

function toggleColorscheme() {
    if(colorscheme == "light") {
        colorscheme = "dark";
    } else {
        colorscheme = "light";
    }

    setColorscheme();
}

window.onload = function() {
    button = document.getElementById("colorscheme-button");

    let saved_colorscheme = getCookie("colorscheme");
    if(saved_colorscheme != "") {
        colorscheme = saved_colorscheme;
    } else {
        colorscheme = "light";
    }

    setColorscheme();
}
