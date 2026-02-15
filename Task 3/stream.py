import cv2
import time
import threading
import base64
import json
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

FRAME_WIDTH = 640
JPEG_QUALITY = 60

outputFrame = None
frameTimestamp = 0
lock = threading.Lock()

def capture_frames():
    global outputFrame, frameTimestamp, lock
    
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    while True:
        success, frame = camera.read()
        if not success:
            time.sleep(0.01)
            continue

        if FRAME_WIDTH:
            height, width = frame.shape[:2]
            aspect_ratio = width / height
            new_height = int(FRAME_WIDTH / aspect_ratio)
            frame = cv2.resize(frame, (FRAME_WIDTH, new_height))

        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
        b64_image = base64.b64encode(buffer).decode('utf-8')
        
        with lock:
            outputFrame = b64_image
            frameTimestamp = time.time()
        
        time.sleep(0.015)

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/get_frame')
def get_frame():
    with lock:
        if outputFrame is None:
            return jsonify({'error': 'No frame available'})
        return jsonify({'image': outputFrame, 'timestamp': frameTimestamp})

@app.route('/time')
def get_time():
    return jsonify({'server_time': time.time()})

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Video Streaming Live</title>
    <style>
        body { background: #1a1a1a; color: #fff; font-family: sans-serif; text-align: center; }
        .container { position: relative; display: inline-block; margin-top: 20px; }
        img { border: 2px solid #444; width: 640px; height: auto; background: #000; }
        
        .overlay {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: #0f0;
            padding: 8px 12px;
            font-size: 1.4rem;
            border-radius: 4px;
            font-weight: bold;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <h1>Live Video Streaming Over Network</h1>
    
    <div class="container">
        <img id="video-stream" src="" alt="Waiting for stream...">
        <div class="overlay" id="latency-display">Calculating...</div>
    </div>

    <script>
        const imgElement = document.getElementById('video-stream');
        const latencyDisplay = document.getElementById('latency-display');
        
        let clockOffset = 0;
        let latencyBuffer = []; // Stores latency values for 1 second

        // 1. Sync Clocks
        async function syncClocks() {
            const start = Date.now();
            const response = await fetch('/time');
            const data = await response.json();
            const end = Date.now();
            
            const networkDelay = (end - start) / 2;
            const serverTimeNow = (data.server_time * 1000) + networkDelay;
            clockOffset = serverTimeNow - Date.now();
        }

        // 2. Main Loop: Fetch Frame & Collect Latency Data
        async function updateFrame() {
            try {
                const startFetch = Date.now();
                const response = await fetch('/get_frame');
                const data = await response.json();

                if (data.image) {
                    imgElement.src = "data:image/jpeg;base64," + data.image;

                    // Calculate instantaneous latency
                    const frameTimeMs = data.timestamp * 1000;
                    
                    // Current time adjusted to Server Timezone
                    const now = Date.now() + clockOffset; 
                    
                    const latency = Math.max(0, now - frameTimeMs);
                    
                    // Add to buffer
                    latencyBuffer.push(latency);
                }
            } catch (error) {
                console.error("Error fetching frame:", error);
            }
            // Repeat as fast as possible for smooth video
            requestAnimationFrame(updateFrame);
        }

        // 3. UI Update Loop (Runs once every 1000ms)
        setInterval(() => {
            if (latencyBuffer.length === 0) return;

            // Calculate Mean (Average)
            const sum = latencyBuffer.reduce((a, b) => a + b, 0);
            const mean = Math.round(sum / latencyBuffer.length);

            // Update Text
            latencyDisplay.innerText = `Latency: ${mean} ms`;

            // Color Coding
            if (mean < 50) latencyDisplay.style.color = "#0f0";       // Green
            else if (mean < 150) latencyDisplay.style.color = "#ff0"; // Yellow
            else latencyDisplay.style.color = "#f00";                 // Red

            // Clear Buffer for next second
            latencyBuffer = [];
            
        }, 1000); // <-- Update every 1 second

        // Start
        syncClocks().then(() => {
            updateFrame();
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    t = threading.Thread(target=capture_frames, daemon=True)
    t.start()
    
    print("--- Server Started ---")
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)