const progressBar = document.getElementById("progressBar");
const loadingText = document.getElementById("loadingText");

const loadingSteps = [
    "Loading Camera Module...",
    "Loading AI Detection Engine...",
    "Connecting Database...",
    "Connecting Alert System...",
    "Initializing ATM Dashboard...",
    "System Ready..."
];

let progress = 0;
let step = 0;

const loading = setInterval(() => {

    progress += 2;

    progressBar.style.width = progress + "%";

    if (progress === 10) loadingText.innerHTML = loadingSteps[0];
    if (progress === 30) loadingText.innerHTML = loadingSteps[1];
    if (progress === 50) loadingText.innerHTML = loadingSteps[2];
    if (progress === 70) loadingText.innerHTML = loadingSteps[3];
    if (progress === 90) loadingText.innerHTML = loadingSteps[4];
    if (progress === 100){

        loadingText.innerHTML = loadingSteps[5];

        clearInterval(loading);

        setTimeout(() => {

            window.location.href = "dashboard.html";

        },1000);

    }

},120);