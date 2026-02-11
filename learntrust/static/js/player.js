const video = document.getElementById("videoPlayer");
const watchPercent = document.getElementById("watchPercent");

let lastTime = 0;

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
