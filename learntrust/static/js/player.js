const video = document.getElementById("videoPlayer");
const watchPercent = document.getElementById("watchPercent");

let lastTime = 0;
let sequenceNumber = 0;
let microQuiz = null;
let quizTriggered = false;

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

// Fetch micro-quiz for this module
async function fetchMicroQuiz() {
    try {
        const response = await fetch(`/api/module/${moduleId}/micro-quiz/`);
        if (response.ok) {
            microQuiz = await response.json();
        }
    } catch (err) {
        console.error('Failed to fetch micro-quiz:', err);
    }
}

// Create quiz modal
function createQuizModal() {
    const modal = document.createElement('div');
    modal.id = 'quizModal';
    modal.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; z-index: 1000;">
            <div style="background: white; padding: 30px; border-radius: 8px; max-width: 500px; width: 90%;">
                <h3>Quiz Question</h3>
                <p id="quizQuestion"></p>
                <div id="quizOptions"></div>
                <div id="quizError" style="color: red; margin-top: 10px; display: none;">Incorrect answer. Please try again.</div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    return modal;
}

// Show quiz modal
function showQuizModal() {
    let modal = document.getElementById('quizModal');
    if (!modal) {
        modal = createQuizModal();
    }
    
    document.getElementById('quizQuestion').textContent = microQuiz.question;
    const optionsDiv = document.getElementById('quizOptions');
    optionsDiv.innerHTML = '';
    
    const options = [
        { key: 'A', text: microQuiz.option_a },
        { key: 'B', text: microQuiz.option_b },
        { key: 'C', text: microQuiz.option_c },
        { key: 'D', text: microQuiz.option_d }
    ];
    
    options.forEach(opt => {
        const btn = document.createElement('button');
        btn.textContent = `${opt.key}. ${opt.text}`;
        btn.style.cssText = 'display: block; width: 100%; margin: 10px 0; padding: 10px; cursor: pointer;';
        btn.onclick = () => submitAnswer(opt.key);
        optionsDiv.appendChild(btn);
    });
    
    document.getElementById('quizError').style.display = 'none';
    modal.style.display = 'flex';
}

// Hide quiz modal
function hideQuizModal() {
    const modal = document.getElementById('quizModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Submit answer
async function submitAnswer(answer) {
    try {
        const response = await fetch('/api/micro-quiz/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken()
            },
            body: `module_id=${moduleId}&answer=${answer}`
        });
        
        const result = await response.json();
        
        if (result.status === 'correct') {
            hideQuizModal();
            video.play();
            quizTriggered = true;
        } else {
            document.getElementById('quizError').style.display = 'block';
        }
    } catch (err) {
        console.error('Failed to submit answer:', err);
    }
}

// Detect tab visibility change
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Tab is hidden - log event and pause video
        console.log('Tab hidden - pausing video');
        video.pause();
        
        // Send visibility event to backend
        fetch('/api/watch-event/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                module_id: parseInt(moduleId),
                event_type: 'tab_hidden',
                sequence_number: ++sequenceNumber,
                current_time: video.currentTime
            })
        }).catch(err => console.error('Visibility event error:', err));
    } else {
        // Tab is visible again - log event
        console.log('Tab visible');
        
        fetch('/api/watch-event/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                module_id: parseInt(moduleId),
                event_type: 'tab_visible',
                sequence_number: ++sequenceNumber,
                current_time: video.currentTime
            })
        }).catch(err => console.error('Visibility event error:', err));
    }
});

// Fetch micro-quiz on load
fetchMicroQuiz();

video.addEventListener("timeupdate", () => {
    // block seeking / fast forward
    if (video.currentTime > lastTime + 0.5) {
        video.currentTime = lastTime;
    }

    lastTime = video.currentTime;

    // calculate watch percentage
    const percent = (video.currentTime / video.duration) * 100;
    watchPercent.innerText = Math.floor(percent);
    
    // Check for micro-quiz trigger
    if (microQuiz && !quizTriggered && Math.floor(video.currentTime) >= microQuiz.trigger_time) {
        video.pause();
        showQuizModal();
    }
});
