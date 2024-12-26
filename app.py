# app.py
import os
import time
import threading
from flask import Flask, request, Response, render_template_string

app = Flask(__name__)

# A simple global to store the latest frame from local detection.
# In production, a queue or more sophisticated data structure might be safer.
latest_frame = None
frame_lock = threading.Lock()

@app.route('/')
def index():
    """Serve a basic HTML page with an <img> that points to /video_feed."""
    html = """
    <html>
      <head><title>Stream</title></head>
      <body>
        <h1>Live Bounding-Boxed Video</h1>
        <img src="/video_feed" width="640" height="480" />
      </body>
    </html>
    """
    return render_template_string(html)

@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    """
    Receives a frame (JPEG bytes) from the local script (test.py) and stores it.
    """
    global latest_frame
    file = request.files.get('frame')  # 'frame' is the key we use in test.py
    if file:
        img_bytes = file.read()
        with frame_lock:
            latest_frame = img_bytes
        return "Frame received", 200
    else:
        return "No frame found", 400

def gen_frames():
    """
    Generator function: yields the latest_frame as MJPEG data.
    """
    while True:
        if latest_frame is not None:
            with frame_lock:
                frame = latest_frame
            # Send the frame as a multipart message
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)  # ~30 FPS max, adjust as needed

@app.route('/video_feed')
def video_feed():
    """MJPEG stream of the bounding-boxed frames."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # For local testing:
    # app.run(host='0.0.0.0', port=5000, debug=True)
    #
    # On Render, you'd typically read the PORT from the environment:
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)