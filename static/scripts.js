let cameraStream;

// Open gallery input and submit automatically
function openGallery() {
    document.getElementById('galleryInput').click();
}

// Open camera
function openCamera() {
    const video = document.getElementById('cameraFeed');
    const captureBtn = document.getElementById('captureBtn');

    navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        cameraStream = stream;
        video.srcObject = stream;
        video.style.display = 'block';
        captureBtn.style.display = 'inline-block';
    })
    .catch(err => {
        alert("Could not access camera: " + err);
    });
}

// Capture image from camera and send to backend
function captureImage() {
    const video = document.getElementById('cameraFeed');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    canvas.toBlob(function(blob) {
        const formData = new FormData();
        formData.append('file', blob, 'capture.jpg');

        fetch('/predict', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text()) // render_template returns HTML
        .then(html => {
            document.open();
            document.write(html);
            document.close();
        })
        .catch(err => console.error(err));
    }, 'image/jpeg');

    // Stop camera
    video.srcObject.getTracks().forEach(track => track.stop());
    video.style.display = 'none';
    document.getElementById('captureBtn').style.display = 'none';
}

// For AR page buttons (History, Overview, Facts, Video)
function showInfo(type) {
    const infoBox = document.getElementById('info-box');
    if(!window.siteData) return;

    if(type === 'video') {
        infoBox.innerHTML = `<iframe width="560" height="315" src="${window.siteData[type]}" frameborder="0" allowfullscreen></iframe>`;
    } else {
        infoBox.innerText = window.siteData[type];
    }
}
