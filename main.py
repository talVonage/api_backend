import sys, os
sys.path.append("vendor")
# import vonage, json

from threading import Lock
from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
import requests
from pprint import pprint

async_mode = None
app = Flask(__name__, template_folder="./ui/templates", static_folder="./ui/static")
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(3)
        count += 1
        price = ((requests.get('https://api.coinbase.com/v2/prices/btc-usd/spot')).json())['data']['amount']
        socketio.emit('my_response',
                      {'data': 'Bitcoin current price (USD): ' + price, 'count': count})

@app.get('/_/health')
async def health():
    return 'OK'
@app.route('/', methods=['GET', 'POST'])
def index():
    global messages
    return render_template('base.html', async_mode=socketio.async_mode, current_user="yoyo")

    """
        if request.method == 'POST':
        print (request)
        print (request.get_json())
        # If it's a POST request, append the JSON data to the messages list
        json_data = request.get_json()

        messages.append(json_data)
    """

@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})
# Receive the test request from client and send back a test response
@socketio.on('test_message')
def handle_message(data):
    print('received message: ' + str(data))
    emit('test_response', {'data': 'Test response sent'})
# Broadcast a message to all clients
@socketio.on('broadcast_message')
def handle_broadcast(data):
    print('received: ' + str(data))
    emit('broadcast_response', {'data': 'Broadcast sent'}, broadcast=True)

@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

"""
@app.route('/inbound', methods=['POST', 'GET'])
def inbound_message():
    print ("Here I got in - inbound !!!")
    data = request.get_json()
    pprint(data)
    return ("200")

@app.route('/status', methods=['POST', 'GET'])
def message_status():
    data = request.get_json()
    pprint(data)
    return ("200")
"""

if __name__ == '__main__':
    port = int(os.getenv('VCR_PORT', 3000))
    #app.run(host="0.0.0.0", port=port)
    socketio.run(app,host="0.0.0.0", port=port, allow_unsafe_werkzeug=True )