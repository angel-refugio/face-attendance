const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const btnToggle = document.getElementById('btnToggle');
const recentCheckins = document.getElementById('recentCheckins');

let stream = null;
let isRunning = false;
let recognitionInterval = null;
let isRecognizing = false;

btnToggle.addEventListener('click', async () => {
    if (isRunning) {
        stopCamera();
    } else {
        await startCamera();
    }
});

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 640, height: 480 } 
        });
        video.srcObject = stream;
        isRunning = true;
        btnToggle.innerHTML = '<i class="bi bi-stop-fill"></i> Detener Camara';
        btnToggle.classList.remove('btn-primary');
        btnToggle.classList.add('btn-danger');
        
        recognitionInterval = setInterval(recognizeFace, 2000);
    } catch (err) {
        alert('Error al acceder a la camara: ' + err.message);
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    if (recognitionInterval) {
        clearInterval(recognitionInterval);
    }
    video.srcObject = null;
    isRunning = false;
    btnToggle.innerHTML = '<i class="bi bi-play-fill"></i> Iniciar Camara';
    btnToggle.classList.remove('btn-danger');
    btnToggle.classList.add('btn-primary');
}

async function recognizeFace() {
    if (!isRunning || isRecognizing) return;
    isRecognizing = true;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const imageData = canvas.toDataURL('image/jpeg', 0.7);

    try {
        const response = await fetch('/camera/api/recognize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imageData })
        });
        
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            data.results.forEach(result => {
                if (result.check_in && result.check_in.success) {
                    addCheckinRecord(result);
                }
            });
        }
    } catch (err) {
        console.error('Error en reconocimiento:', err);
    } finally {
        isRecognizing = false;
    }
}

function addCheckinRecord(result) {
    const now = new Date();
    const timeStr = result.check_in.time || now.toLocaleTimeString();
    const statusClass = result.check_in.status === 'on_time' ? 'success' : 'warning';
    const statusText = result.check_in.status === 'on_time' ? 'Puntual' : 'Tarde';
    
    const recordHtml = `
        <div class="alert alert-${statusClass} alert-dismissible fade show" role="alert">
            <strong>${result.employee_name}</strong>
            <br><small>${timeStr} - Confianza: ${result.confidence}%</small>
            <br><span class="badge bg-${statusClass}">${statusText}</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    if (recentCheckins.querySelector('.text-muted')) {
        recentCheckins.innerHTML = '';
    }
    
    recentCheckins.insertAdjacentHTML('afterbegin', recordHtml);
    
    const alerts = recentCheckins.querySelectorAll('.alert');
    if (alerts.length > 10) {
        alerts[alerts.length - 1].remove();
    }
}
