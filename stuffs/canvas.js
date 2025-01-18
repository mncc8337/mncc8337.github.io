var canvas;
var canvas_context;

window.addEventListener('load', function() {
    canvas = document.getElementById("canvas");
    canvas_context = canvas.getContext("2d");

    canvas_context.moveTo(0, 0);
    canvas_context.lineTo(200, 100);

    canvas_context.fillText("ngu", 10, 50);
    canvas_context.stroke();
});
