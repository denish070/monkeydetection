from flask import Flask, request, Response
import base64
import time
import threading
import queue

app = Flask(__name__)

# Store frames in a queue (or a ring buffer)
FRAME_QUEUE = queue.Queue(maxsize=300)

@app.route('/upload_batch', methods=['POST'])
def upload_batch():
    """
    Receives JSON with an array of base64-encoded frames.
    """
    data = request.json
    if not data or 'frames' not in data:
        return "Invalid payload", 400
    
    for b64 in data['frames']:
        frame_bytes = base64.b64decode(b64)
        # Put them in the server's queue
        try:
            FRAME_QUEUE.put(frame_bytes, timeout=1)
        except:
            # If full, discard or handle differently
            pass

    return "Batch received", 200

def frame_generator():
    """
    Yields frames from FRAME_QUEUE at a consistent FPS (say 10–15).
    """
    while True:
        try:
            # get block or add a small timeout
            frame = FRAME_QUEUE.get(timeout=5)
        except:
            # If no frames, just yield a blank or continue
            time.sleep(0.1)
            continue
        
        # yield as MJPEG
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        # Control the playback rate
        time.sleep(0.07)  # ~14 FPS

@app.route('/video_feed')
def video_feed():
    """Serve a continuous MJPEG stream of frames from FRAME_QUEUE."""
    return Response(frame_generator(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    # Simple HTML to view the stream
    return """
    <html>
      <body>
        <h1>Buffered Video Stream</h1>
        <img src="/video_feed" />
      </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)