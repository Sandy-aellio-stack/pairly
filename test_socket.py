import socketio

sio = socketio.Client()

@sio.event
def connect():
    print("connection established")

@sio.event
def connect_error(err):
    print("connection failed", err)

@sio.event
def disconnect():
    print("disconnected")

try:
    sio.connect('http://localhost:8000', socketio_path="/socket.io", transports=['websocket'], auth={'token': 'test_token'})
    print("Connected? ", sio.connected)
    sio.disconnect()
except Exception as e:
    print("Error:", e)
