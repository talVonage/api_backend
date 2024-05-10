print ("Hallo")

"""


import sys
import os
sys.path.append("vendor")
import json
import uvicorn
import asyncio

from vonage_cloud_runtime.providers.messages.messages import Messages
from vonage_cloud_runtime.providers.messages.contracts.messageContact import MessageContact
from vonage_cloud_runtime.providers.messages.messages

from fastapi import Request, FastAPI
from nerualpha.neru import Neru
from nerualpha.providers.messages.messages import Messages
from nerualpha.providers.messages.contracts.messageContact import MessageContact
from nerualpha.providers.messages.contracts.smsMessage import SMSMessage

app = FastAPI()
neru = Neru()

vonageContact = MessageContact()
vonageContact.type_ = 'sms'
vonageContact.number = os.getenv('VONAGE_NUMBER')

async def setupListeners():
    try:
        session = neru.createSession()
        messages = Messages(session)

        fromContact = MessageContact()
        fromContact.type_ = 'sms'
        fromContact.number = None

        await messages.onMessage('onMessage', fromContact, vonageContact).execute()
        await messages.onMessageEvents('onEvent', fromContact, vonageContact).execute()

    except Exception as e:
        print(e)
        sys.exit(1)

@app.get('/_/health')
async def health():
    return 'OK'

@app.post('/onMessage')
async def onMessages(request: Request):
    session = neru.createSession()
    messages = Messages(session)

    body = await request.json()
    text = body['text']
    calleeNumber = body['from']

    message = SMSMessage()
    message.to = calleeNumber
    message.from_ = vonageContact.number
    message.channel = vonageContact.type_
    message.message_type = 'text'
    message.text = f"You sent: {text}"

    await messages.send(message).execute()
    return 'OK'

@app.post('/onEvent')
async def onEvent(request: Request):
    body = await request.json()
    print('message status is:', body['status'])
    return 'OK'

if __name__ == "__main__":
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.run_until_complete(setupListeners())
    port = int(os.getenv('NERU_APP_PORT'))
    uvicorn.run(app, host="0.0.0.0", port=port)


"""