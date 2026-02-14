const video = document.getElementById("videoPlayer");
const watchPercent = document.getElementById("watchPercent");

let lastTime = 0;
let sequenceNumber = 0;

// Get module_id from data attribute or URL
const moduleId = video.dataset.moduleId || window.location.pathname.split('/')[2];

// Get CSRF token from cookie
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Send heartbeat event
function sendHeartbeat() {
    sequenceNumber++;
    
    fetch('/api/watch-event/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            module_id: parseInt(moduleId),
            event_type: 'heartbeat',
            sequence_number: sequenceNumber
        })
    }).catch(err => console.error('Heartbeat error:', err));
}

// Send heartbeat every 10 seconds
setInterval(sendHeartbeat, 10000);

video.addEventListener("timeupdate", () => {
    // block seeking / fast forward
    if (video.currentTime > lastTime + 0.5) {
        video.currentTime = lastTime;
    }

    lastTime = video.currentTime;

    // calculate watch percentage
    const percent = (video.currentTime / video.duration) * 100;
    watchPercent.innerText = Math.floor(percent);
});
