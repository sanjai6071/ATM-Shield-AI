const video = document.getElementById("liveCamera");
const canvas = document.getElementById("captureCanvas");
let helmetTimer = null;
let warningActive = false;
let atmLocked = false;
let currentThreatObject = null;
window.addEventListener("DOMContentLoaded", async () => {

    const countdown = document.getElementById("countdown");


    try {

        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false
        });

       video.srcObject = stream;

await video.play();

console.log("ATM Camera Started");
console.log(video.videoWidth, video.videoHeight);
    } catch (error) {

        console.error("Camera Error:", error);

        alert(error.message);

    }

});
function updateTime(){

    const now = new Date();

    document.getElementById("currentTime").innerHTML =
        now.toLocaleString();

}

setInterval(updateTime,1000);

updateTime();
// =========================
// LIVE DATE & TIME
// =========================

function updateTime(){

    const now = new Date();

    document.getElementById("currentTime").innerHTML =
        now.toLocaleString();

}

setInterval(updateTime,1000);

updateTime();
// =========================
// VOICE WARNING SYSTEM
// =========================

const testVoiceBtn = document.getElementById("testVoiceBtn");

testVoiceBtn.addEventListener("click", () => {

    const speech = new SpeechSynthesisUtterance();

    speech.text = "Warning. Helmet detected. Please remove your helmet immediately.";

    speech.lang = "en-US";

    speech.rate = 1;

    speech.pitch = 1;

    speech.volume = 1;

    window.speechSynthesis.speak(speech);

});

// =========================================
// SYSTEM STARTUP NOTIFICATION
// =========================================

window.addEventListener("load", () => {

    const notification = document.getElementById("systemNotification");

    // Show notification after 1 second
    setTimeout(() => {

        notification.classList.add("show");

    }, 1000);

    // Hide notification after 5 seconds
    setTimeout(() => {

        notification.classList.remove("show");

    }, 5000);

});

// =========================================
// SPEAK FUNCTION
// =========================================

function speak(message, language = "en-US") {

    const speech = new SpeechSynthesisUtterance(message);

    speech.lang = language;
    speech.rate = 1;
    speech.pitch = 1;
    speech.volume = 1;

    window.speechSynthesis.speak(speech);
}

// =========================================
// THREAT-SPECIFIC VOICE MESSAGES
// =========================================

function getThreatVoice(object, peopleCount = 0) {

    if (peopleCount >= 4) {
        return "Warning. Too many people detected. Please ask other persons to leave the ATM.";
    }

    switch (object) {

        case "HELMET":
        case "With Helmet":
            return "Warning. Helmet detected. Please remove your helmet immediately.";

        case "FACE MASK":
        case "mask":
            return "Warning. Face covering detected. Please uncover your face.";

        case "WEAPON":
            return "Warning. Dangerous weapon detected. Please put the weapon down and move away immediately.";

        case "knife":
            return "Warning. Knife detected. Please put the knife down and move away from the ATM.";

        case "gun":
        case "weapon":
            return "Warning. Dangerous weapon detected. Please put the weapon down and move away immediately.";

        case "scissors":
            return "Warning. Suspicious object detected. Please put it down and move away from the ATM.";

        default:
            return "Warning. Suspicious activity detected. Please move away from the ATM.";
    }
}


// =========================================
// TAMIL THREAT-SPECIFIC VOICE MESSAGES
// =========================================

function getTamilThreatVoice(object, peopleCount = 0) {

    if (peopleCount >= 4) {
        return "எச்சரிக்கை. அதிகமான நபர்கள் கண்டறியப்பட்டுள்ளனர். தயவுசெய்து மற்ற நபர்களை ATM பகுதியிலிருந்து வெளியேறச் சொல்லுங்கள்.";
    }

    switch (object) {

        case "HELMET":
            return "எச்சரிக்கை. ஹெல்மெட் கண்டறியப்பட்டுள்ளது. தயவுசெய்து ஹெல்மெட்டை உடனடியாக அகற்றவும்.";

        case "FACE MASK":
            return "எச்சரிக்கை. முகக்கவசம் கண்டறியப்பட்டுள்ளது. தயவுசெய்து உங்கள் முகத்தை வெளிப்படுத்தவும்.";

        case "WEAPON":
            return "எச்சரிக்கை. ஆபத்தான ஆயுதம் கண்டறியப்பட்டுள்ளது. தயவுசெய்து ஆயுதத்தை கீழே வைத்து உடனடியாக விலகிச் செல்லவும்.";

        case "knife":
            return "எச்சரிக்கை. கத்தி கண்டறியப்பட்டுள்ளது. தயவுசெய்து கத்தியை கீழே வைத்து ATM-இலிருந்து விலகிச் செல்லவும்.";

        case "gun":
        case "weapon":
            return "எச்சரிக்கை. ஆபத்தான ஆயுதம் கண்டறியப்பட்டுள்ளது. தயவுசெய்து ஆயுதத்தை கீழே வைத்து உடனடியாக விலகிச் செல்லவும்.";

        default:
            return "எச்சரிக்கை. சந்தேகத்திற்கிடமான செயல்பாடு கண்டறியப்பட்டுள்ளது. தயவுசெய்து ATM-இலிருந்து விலகிச் செல்லவும்.";
    }
}

// =========================================
// CAPTURE AND SAVE SECURITY EVIDENCE
// =========================================

async function captureEvidence() {

    const ctx = canvas.getContext("2d");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );

    const image = canvas.toDataURL("image/png");

    try {

        const response = await fetch("/save_evidence", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                image: image
            })

        });

        const data = await response.json();

        if (data.success) {

            console.log("✅ Evidence saved:", data.filename);

            return data.filename;

        } else {

            console.error("❌ Evidence save failed");

            return null;
        }

    } catch (error) {

        console.error("❌ Evidence save error:", error);

        return null;
    }
}

// =========================================
// EMERGENCY ALERT SYSTEM
// =========================================

const alertPopup = document.getElementById("alertPopup");
const countdown = document.getElementById("countdown");
const atmMessage = document.getElementById("atmMessage");
const incidentLog = document.getElementById("incidentLog");
const voiceButton = document.getElementById("testVoiceBtn");


/*

voiceButton.addEventListener("click", () => {

    // Show popup
    alertPopup.classList.add("show");
    addLog("🟡 Helmet Detected");
    atmMessage.innerHTML = `
⚠ SECURITY WARNING <br><br>
Helmet Detected <br><br>
Please Remove Helmet
`;

    let timeLeft = 20;

    // Voice warnings

    const timer = setInterval(() => {

 countdown.innerHTML = timeLeft;

switch(timeLeft){

    case 15:
        speak("Attention. Fifteen seconds remaining to comply.");
        break;

    case 10:
        speak("Final warning. Security personnel will be notified.");
        break;

    case 5:
        speak("Security action will begin in five seconds.");
        break;
}

timeLeft--;

countdown.innerHTML = timeLeft;

if (timeLeft <= 0) {
    addLog("🔴 ATM Locked");

    clearInterval(timer);
    captureEvidence();

    // Change ATM Display
    atmMessage.innerHTML = `
    🔒 ATM LOCKED <br><br>
    Security Team Notified <br><br>
    Transaction Cancelled
    `;

    // Close popup after 2 seconds
    setTimeout(() => {

        alertPopup.classList.remove("show");

    }, 2000);

}

}, 1000);   // <-- Close setInterval

});   // <-- Close addEventListener

*/


// =========================================
// INCIDENT LOG FUNCTION
// =========================================

function addLog(message){

    const time = new Date().toLocaleTimeString();

    incidentLog.innerHTML += `<p>${time} - ${message}</p>`;

    incidentLog.scrollTop = incidentLog.scrollHeight;

}

// =========================================
// AI SECURITY TIMER
// =========================================

async function startSecurityTimer(
    threatObject = "suspicious activity",
    peopleCount = 0,
 confidence = 0
)
 {

    if (helmetTimer) return;

    let timeLeft = 10;

    document.getElementById("timer").innerText = timeLeft;

    // First warning
   speak(getTamilThreatVoice(threatObject, peopleCount), "ta-IN");

setTimeout(() => {
    speak(getThreatVoice(threatObject, peopleCount), "en-US");
}, 3000);



   helmetTimer = setInterval(async () => {

        timeLeft--;

        document.getElementById("timer").innerText = timeLeft;

     // Repeat warning at important countdown points
if (timeLeft === 15 || timeLeft === 10 || timeLeft === 5) {

    speak(getThreatVoice(threatObject, peopleCount));

}

        // Countdown finished
        if (timeLeft <= 0) {
            atmLocked = true;
            const evidenceFile = await captureEvidence();

            fetch("/save_incident", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        threat_type: threatObject,
        confidence: confidence,
        threat_level: threatObject === "knife" ? "HIGH" : "MEDIUM",
        threat_score: threatObject === "knife" ? 95 : 70,
        status: "ATM LOCKED",
        evidence_file: evidenceFile || "evidence_failed.png"
    })
})
.then(response => response.json())
.then(result => {
    console.log("Incident saved:", result);
})
.catch(error => {
    console.error("Incident save error:", error);
});
            // Save real security incident


            clearInterval(helmetTimer);
            helmetTimer = null;

            document.getElementById("atmMessage").innerHTML = `
                🔒 ATM LOCKED <br><br>
                Transaction Blocked <br><br>
                Security Team Notified
            `;

            document.getElementById("atmStatus").innerText = "LOCKED";

            addLog("🔴 ATM Locked");

            speak(
                "Security warning. The ATM has been locked. Security personnel have been notified."
            );

        }

    }, 1000);
}

// =========================================
// AI DETECTION SYSTEM
// =========================================

async function detectAI() {
   

    const video = document.getElementById("liveCamera");
    const canvas = document.getElementById("captureCanvas");

    if (!video || !canvas) return;

    const ctx = canvas.getContext("2d");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.drawImage(video, 0, 0);

   canvas.toBlob(async (blob) => {

    if (!blob) {
        console.log("Waiting for camera...");
        return;
    }

    const formData = new FormData();
    formData.append("frame", blob, "frame.jpg");

        try {

            const response = await fetch("/detect", {
                method: "POST",
                body: formData
            });

           const data = await response.json();
const detections = data.detections || [];

drawDetections(detections);

console.table(detections);

let people = detections.filter(
    item => item.object === "person"
).length;

document.getElementById("peopleCount").innerText = people;

if (people <= 3 && warningActive && currentThreatObject === "person") {
    clearInterval(helmetTimer);
    helmetTimer = null;
    warningActive = false;

    document.getElementById("timer").innerText = "20";

    document.getElementById("atmMessage").innerHTML = `
        Welcome to Zenith Bank<br>
        Please insert your ATM card.
    `;

    console.log("People count safe. Security timer stopped.");
}

// =========================================
// TOO MANY PEOPLE DETECTION
// =========================================

if (people >= 4 && !warningActive) {
    currentThreatObject = "person";

    warningActive = true;

    document.getElementById("atmMessage").innerHTML = `
        ⚠ SECURITY WARNING <br><br>
        TOO MANY PEOPLE DETECTED <br><br>
        Maximum 3 Persons Allowed<br><br>
        Please Ask Other Persons To Leave
    `;

    addLog("🟠 Too Many People Detected");

    startSecurityTimer("person", people, 0);

    console.log("Too many people security warning started");
}
if (detections.length > 0) {

    const threatItem = detections.find(item =>
        item.object === "knife"
    );

    const displayItem = threatItem || detections[0];

    const obj = displayItem.object;
    const conf = displayItem.confidence;

    document.getElementById("objectName").innerText = obj;
    document.getElementById("confidence").innerText = conf + "%";

    // Default values
    let threat = "🟢 SAFE";
    let score = 15;

// Future dangerous objects
if (obj === "knife") {

    threat = "🔴 HIGH";
    score = 95;

    if (!warningActive) {

        warningActive = true;

        document.getElementById("atmMessage").innerHTML = `
            ⚠ SECURITY WARNING <br><br>
            KNIFE DETECTED <br><br>
            Please Put The Knife Down
        `;

        addLog("🔴 KNIFE Object Detected");

        startSecurityTimer(obj, people, conf);

        console.log("Knife security warning started");
    }
}

if (obj === "helmet") {

    threat = "🟠 MEDIUM";
    score = 70;

    if (!warningActive) {

        warningActive = true;

        document.getElementById("atmMessage").innerHTML = `
            ⚠ SECURITY WARNING <br><br>
            HELMET DETECTED <br><br>
            Please Remove Your Helmet
        `;

        addLog("🟠 HELMET Detected");

        startSecurityTimer(obj, people, conf);

        console.log("Helmet security warning started");
    }
}

if (obj === "mask" || obj === "face covering") {

    threat = "🟠 MEDIUM";
    score = 75;

    if (!warningActive) {

        warningActive = true;

        document.getElementById("atmMessage").innerHTML = `
            ⚠ SECURITY WARNING <br><br>
            FACE COVERING DETECTED <br><br>
            Please Uncover Your Face
        `;

        addLog("🟠 FACE COVERING Detected");

        startSecurityTimer("mask", people, conf);

        console.log("Face covering security warning started");
    }
}

if (
    obj === "gun" ||
    obj === "weapon" ||
    obj === "pistol"
) {

    threat = "🔴 CRITICAL";
    score = 100;

    if (!warningActive) {

        warningActive = true;

        document.getElementById("atmMessage").innerHTML = `
            ⚠ SECURITY WARNING <br><br>
            DANGEROUS WEAPON DETECTED <br><br>
            Please Put The Weapon Down<br>
            Move Away From The ATM
        `;

        addLog("🔴 DANGEROUS WEAPON Detected");

        startSecurityTimer(obj, people, conf);

        console.log("Dangerous weapon security warning started");
    }
}



if (obj === "person" && !atmLocked) {

    threat = "🟢 SAFE";
    score = 15;

    document.getElementById("atmMessage").innerHTML = `
        Welcome to Zenith Bank<br>
        Please insert your ATM card.
    `;
}

document.getElementById("riskLevel").innerText = threat;
document.getElementById("score").innerText = score;
document.getElementById("threatLevel").innerText = threat;

// =========================================
// THREAT REMOVED CHECK
// =========================================

const knifePresent = detections.some(item => item.object === "knife");

const helmetPresent = detections.some(item => item.object === "helmet");

const maskPresent = detections.some(
    item => item.object === "mask"
);

const weaponPresent = detections.some(
    item =>
        item.object === "gun" ||
        item.object === "weapon" ||
        item.object === "pistol"
);

const tooManyPeople = people >= 4;

const threatStillPresent =
    knifePresent ||
    helmetPresent ||
    maskPresent ||
    weaponPresent ||
    tooManyPeople;

if (!threatStillPresent && warningActive) {

    warningActive = false;

    if (helmetTimer) {

        clearInterval(helmetTimer);
        helmetTimer = null;

    }

    document.getElementById("timer").innerText = "";

    window.speechSynthesis.cancel();

    document.getElementById("atmMessage").innerHTML = `
        Welcome to Zenith Bank<br>
        Please insert your ATM card.
    `;

    addLog("🟢 Threat Removed");

    console.log("Security threat removed. Timer stopped.");

    const threatType = data.threat_type || "NONE";
const threatLevel = data.threat_level || "SAFE";

let displayItem =
    detections.find(item => item.object === "knife") ||
    detections.find(item => item.object === "Without Helmet") ||
    detections.find(item => item.object === "mask") ||
    detections.find(item => item.object === "person");

if (displayItem) {
    document.getElementById("objectName").innerText =
        displayItem.object;

    document.getElementById("confidence").innerText =
        displayItem.confidence + "%";
} else {
    document.getElementById("objectName").innerText = "None";
    document.getElementById("confidence").innerText = "0%";
}


// =========================================
// THREAT LEVEL
// =========================================

let threat = "🟢 SAFE";
let score = 15;

if (threatLevel === "CRITICAL") {
    threat = "🔴 CRITICAL";
    score = 100;
}
else if (threatLevel === "HIGH") {
    threat = "🟠 HIGH";
    score = 80;
}

document.getElementById("riskLevel").innerText = threat;
document.getElementById("score").innerText = score;
document.getElementById("threatLevel").innerText = threat;


// =========================================
// SECURITY WARNING
// =========================================

if (!threatStillPresent && warningActive && !helmetTimer) {

    warningActive = true;
    currentThreatObject = threatType;

    let warningMessage = "";

    if (threatType === "WEAPON") {

        warningMessage = `
            ⚠ SECURITY WARNING <br><br>
            🔴 KNIFE / WEAPON DETECTED <br><br>
            Please move away from the ATM
        `;

    }
    else if (threatType === "NO HELMET") {

        warningMessage = `
            ⚠ SECURITY WARNING <br><br>
            🟠 NO HELMET DETECTED <br><br>
            Please remove your helmet
        `;

    }
    else if (threatType === "FACE MASK") {

        warningMessage = `
            ⚠ SECURITY WARNING <br><br>
            🟠 FACE MASK DETECTED <br><br>
            Please uncover your face
        `;

    }

    document.getElementById("atmMessage").innerHTML =
        warningMessage;

    addLog("⚠ " + threatType + " DETECTED");

    startSecurityTimer(
        threatType,
        people,
        displayItem ? displayItem.confidence : 0
    );

    console.log(
        "Security warning started:",
        threatType
    );
}


// =========================================
// THREAT REMOVED
// =========================================

if (threatType === "NONE" &&
    warningActive &&
    currentThreatObject !== "person" &&
    !helmetTimer) {

    warningActive = false;

    if (helmetTimer) {
        clearInterval(helmetTimer);
        helmetTimer = null;
    }

    document.getElementById("timer").innerText = "20";

    window.speechSynthesis.cancel();

    document.getElementById("atmMessage").innerHTML = `
        Welcome to Zenith Bank<br>
        Please insert your ATM card.
    `;

    addLog("🟢 Threat Removed");

    console.log("Security threat removed.");
}
}

}
        } catch (err) {

            console.error("AI Error:", err);

        }

    }, "image/jpeg");

}



// Run AI every second
setInterval(detectAI, 1000);

// =========================================
// HIDDEN AI DETECTION DISPLAY
// =========================================

function drawDetections(data) {

    const canvas = document.getElementById("detectionCanvas");

    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    ctx.clearRect(0, 0, canvas.width, canvas.height);
}



speechSynthesis.getVoices().forEach(v => {
    console.log(v.name, v.lang);
});


function testTamilVoice() {
    const speech = new SpeechSynthesisUtterance(
        "எச்சரிக்கை. ஹெல்மெட் கண்டறியப்பட்டுள்ளது."
    );

    speech.lang = "ta-IN";
    speech.rate = 1;
    speech.pitch = 1;
    speech.volume = 1;

    window.speechSynthesis.speak(speech);
}