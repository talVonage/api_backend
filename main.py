# import vonage
import sys, os
sys.path.append("vendor")
#import json
import asyncio

from flask import Flask, request, jsonify
from pprint import pprint

app = Flask(__name__)

print ("hallo")

@app.route('/')
def hello():
    return 'Hello, World!'

@app.get('/_/health')
async def health():
    return 'OK'


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

if __name__ == '__main__':
    port = int(os.getenv('VCR_PORT'))
    app.run(host="0.0.0.0", port=port)