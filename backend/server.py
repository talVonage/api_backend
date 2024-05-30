import json
import sys, os, time
import jinja2

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

sys.path.append("vendor")
# import vonage, json
import logging
logging.basicConfig(level=logging.DEBUG)

from threading import Lock, Event
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
from flask_session import Session
from asset import Asset

from my_tools.config import Config
from my_tools.globals import get_not_none
from my_tools.backend_ui_api import Backend_Ui_Api
from my_tools.mng_elk import Elk

env=jinja2.Environment()
env.policies['json.dumps_kwargs'] = {'sort_keys': False}

app = Flask(__name__, template_folder="../ui/templates", static_folder="../ui/static")
app.config['SESSION_TYPE'] = 'filesystem'               # You can use other backends like 'redis', 'memcached', etc.
app.config['SESSION_FILE_DIR'] = './flask_session/'     # Directory to store session files
app.config['SESSION_PERMANENT'] = False                 # Optional: control session persistence
Session(app)

Asset(app)


socketio = SocketIO(app, async_mode=None)
thread = None
thread_lock = Lock()
thread_event = Event()

""" Global variables """
von_api = Backend_Ui_Api()

def connect_api ():
    if von_api.is_api_connect:
        session["connect"] = True
        return session["connect"], f"Connected To Vonage, API Key:{von_api.app_key}"

    is_form = bool(request.form)
    if is_form and not von_api.is_api_connect:
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_sec')

        if api_key and len(api_key)>0 and api_secret and len(api_secret)>0:
            session["key"] = api_key
            session["secret"] = api_secret
            von_api.connect_api(api_key=api_key, api_secret=api_secret)
            if von_api.is_api_connect:
                session["connect"]=True
                return session["connect"], f"Connected To Vonage, API Key:{von_api.app_key}"
            else:
                return False, f"Error connecting to Vonage API using {api_key} key"

    return False, "Not Connected To Vonage API"

""" Application routes  """
@app.get('/_/health')
async def health():
    return 'OK'

@app.route('/', methods=['GET', 'POST'])
def index():
    is_connected, msg_conn = connect_api ()
    print ("TAL" , is_connected, msg_conn)
    api_keys = von_api.subapi
    phone_numbers = von_api.all_numbers
    apps = von_api.apps

    return render_template('main.html',
                           msg_dict={},
                           async_mode=socketio.async_mode,
                           api_keys=api_keys,
                           numbers=phone_numbers,
                           apps=apps,
                           is_connected = is_connected,
                           msg_conn=msg_conn)

""" Submit api key and secret """
@app.route('/submit_api', methods=['POST'])
def submit_api():
    is_connected, msg_conn = connect_api()
    api_keys = von_api.subapi
    phone_numbers = von_api.all_numbers
    apps = von_api.apps


    return render_template('main.html',
                           msg_dict={},
                           async_mode=socketio.async_mode,
                           api_keys=api_keys,
                           numbers=phone_numbers,
                           apps=apps,
                           is_connected = is_connected,
                           msg_conn = msg_conn)

@app.route('/sms')
def sms():
    is_connected, msg_conn = connect_api()
    return render_template('sms.html',
                           is_connected=is_connected,
                           msg_conn=msg_conn,
                           msg_dict={})

@app.route('/verify')
def verify():
    is_connected, msg_conn = connect_api()
    return render_template('verify.html',is_connected=is_connected,
                           msg_conn=msg_conn,
                           msg_dict={})

@app.route('/voice')
def voice():
    is_connected, msg_conn = connect_api()
    return render_template('voice.html',is_connected=is_connected,
                           msg_conn=msg_conn,
                           msg_dict={})

@app.route('/wa_templates')
def wa_templates():
    is_connected, msg_conn = connect_api()
    all_templates, all_ex_account = {}, []


    if is_connected:
        all_ex_account = von_api.get_external_account(provider="whatsapp")
        if all_ex_account and len(all_ex_account)>0 and not von_api.waba_id:
            von_api.waba_id = all_ex_account[0][1]          #WABA ID FROM LIST OF LISTS
        all_templates = von_api.wa_templates_get()

    return render_template('wa_template.html', all_templates=all_templates,
                           wa_categories=von_api.WA_CATEGORIES,
                           wa_lang=von_api.WA_LANGUAGES,
                           msg_dict={},
                           all_ex_account=all_ex_account,
                           is_connected=is_connected,
                           msg_conn=msg_conn)

@app.route('/submit_waba', methods=['POST'])
def submit_waba():
    is_connected, msg_conn = connect_api()
    waba_id       = request.form.get('wa_waba')
    if waba_id and len(waba_id)>0:
        von_api.waba_id = waba_id
        msg = {von_api.RESPONSE_SUCCESS:f"Using WABA ID {waba_id}"}
    else:
        msg = {von_api.RESPONSE_FAILED: f"Failed to upload  WABA ID "}
    all_templates, all_ex_account = {}, []

    if von_api.is_api_connect:
        all_templates = von_api.wa_templates_get()
        all_ex_account= von_api.get_external_account(provider="whatsapp")

    return render_template('wa_template.html', all_templates=all_templates,
                           wa_categories=von_api.WA_CATEGORIES,
                           wa_lang=von_api.WA_LANGUAGES,
                           msg_dict=msg,
                           all_ex_account=all_ex_account,
                           is_connected=is_connected,
                           msg_conn=msg_conn)



    return {von_api.RESPONSE_SUCCESS: f"{str(waba_id)}\n\n Hello world! "}

    #render_template('messages.html',
    #                       all_templates=[],
    #                       wa_categories=von_api.WA_CATEGORIES,
    #                       wa_lang=von_api.WA_LANGUAGES,
    #                       msg_dict={von_api.RESPONSE_SUCCESS: f"<span>{str(waba_id)}<span><br>"})

@app.route('/submit_wa', methods=['POST'])
def submit_wa():
    selected_name       = request.form.get('wa_combobox')
    selected_component  = request.form.get('json_template')
    selected_lang       = request.form.get('wa_lang')
    selected_category   = request.form.get('wa_category')

    res = von_api.wa_update_template(name=selected_name, component=selected_component)
    print (res)

    all_templates = von_api.wa_get_templates()

    return render_template('wa_template.html', all_templates=all_templates,
                           wa_categories=von_api.WA_CATEGORIES,
                           wa_lang=von_api.WA_LANGUAGES,
                           msg_dict=res)

@app.route('/tech')
def tech():
    is_connected, msg_conn = connect_api()
    phone_numbers = von_api.all_numbers
    return render_template('tech.html',
                           all_numbers=phone_numbers,
                           msg_dict={},
                           is_connected=is_connected,
                           msg_conn=msg_conn)

@app.route('/tech_reg_validate_number', methods=['POST'])
def tech_reg_number ():
    num = request.data.decode('utf-8')
    res = von_api.wa_embedded_valid_number(number=num)
    return res

@app.route('/tech_reg_load_numbers', methods=['POST'])
def tech_reg_load_numbers ():
    country = request.get_json().get('country')
    numbers = []
    if country and len(country)>0:
        numbers=von_api.get_numbers_to_buy (country)
        if numbers and len(numbers)>0:
            numbers = [num[0] for num in numbers]

    return jsonify(numbers)

@app.route('/tech_reg_call_foreword', methods=['POST'])
def tech_reg_call_foreword ():
    data = request.get_json()
    from_number = data.get("from")
    to_number = data.get("to")
    res = von_api.wa_embedded_call_foreword (from_number, to_number, to_disable=False)
    return res

@app.route('/tech_reg_call_foreword_disabled', methods=['POST'])
def tech_reg_call_foreword_disabled ():
    data = request.get_json()
    from_number = data.get("from")
    to_number = data.get("to")
    res = von_api.wa_embedded_call_foreword (from_number, to_number, to_disable=True)
    return res

@app.route('/tech_reg', methods=['GET', 'POST'])
def tech_reg ():
    wa_code = request.get_json()
    status  = wa_code.get('status')
    resp    = wa_code.get('authResponse')

    ret_json = {"msg": f"WA RESPONSE \n {wa_code}", "id": "", "numbers": []}
    if resp and "code" in resp:
        exchange_code = resp["code"]
        resp = von_api.wa_embedded_debug_token (exchange_code=exchange_code)
        ret_json = resp if resp and len(resp)>0 else ret_json

    print (f"SERVER: EMBEDDED SIGN UP RESPONSE: {ret_json}")
    return json.dumps(ret_json)

@app.route('/update_application', methods=['GET', 'POST'])
def update_application ():
    is_connected = False
    msg_conn = "Not Connected To Any Vonage Application"
    uploaded_file = request.files['file']

    if uploaded_file:
        file_name = uploaded_file.filename
        if file_name and len(file_name)>0:
            file_content = uploaded_file.read()
            print (f"file content loaded successfully, name: {file_name}")
            all_templates = von_api.wa_get_templates(app_id='xxxx', app_secret=file_content)
            all_apps = von_api.apps_by_capabilites(capability="messages")

            return render_template('messages.html', all_templates=all_templates,
                                   wa_categories=von_api.WA_CATEGORIES,
                                   wa_lang=von_api.WA_LANGUAGES,
                                   msg_dict={},
                                   all_apps=all_apps,
                                   is_connected=is_connected,
                                   msg_conn=msg_conn)
    else:
        return "No file uploaded!"



""" WEBHOOKS VONAGE API"""
@app.route('/webhooks/delivery', methods=['POST'])
def sms_delivery():
    print ("** SMS Delivery Webhook **")
    data = request.get_json()
    print (data)
    socketio.emit('response_sms', f"SMS DELIVERY >>>>  {str(data)} ")
    return f"Done !"

@app.route('/webhooks/inbound', methods=['POST'])
def sms_inbound():
    print ("** SMS Delivery Webhook **")
    data = request.get_json()
    print (data)
    socketio.emit('response_sms', f"SMS INBOUND >>>>  {str(data)} ")
    return ("message_status", 200)


""" Sockets / Real time events"""
@socketio.on('submit_sms')
def handle_submit(data):
    api_key     = get_not_none (data.get('api_key'),Config.API_KEY)
    api_secret  = get_not_none (data.get('api_sec'), Config.API_SECRET)
    send_from   = data.get('send_from')
    send_to     = data.get('send_to')
    msg         = data.get('msg')
    is_sdk= data.get('is_sdk')

    if is_sdk:
        resp = von_api.sms_send_sdk(send_from=send_from, send_to=send_to, msg=msg)
    else:
        resp = von_api.sms_send_restapi(send_from=send_from, send_to=send_to, msg=msg)

    logging.info (f"SEND SMS RESPONSE: {resp}")

    # Emit a message to the connected clients using SocketIO
    socketio.emit('response_sms', resp )

    # Add ELK Data
    if von_api.msg_id is not None:
        global thread
        with thread_lock:
            if thread is None:
                thread_event.set()
                thread = socketio.start_background_task( elk_thread, api_key, von_api.msg_id, thread_event, 100)

    # You can also emit to a specific client using 'room' argument
    # socketio.emit('log', f"Form submitted - Username: {username}, Phone: {phone}", room=request.sid)

"""" OLD VERSION !!!!  
@app.route('/sms_send', methods=['POST'])
def sms_send():
    msg_from= request.form['from']
    msg_to  = request.form['to']
    msg_text= request.form['msg']

    print ("TAL ")
    print (msg_to, msg_from, msg_text)

    socketio.emit('submit_event', f"YYYYYY Form submitted - Username: {msg_from}, Phone: {msg_text}")

    return redirect(url_for('sms'))
    #return render_template('sms.html',msg_list=['olla','walla'])

@socketio.on('custom_event')
def handle_custom_event(data):
    # Process the data (you can replace this with your backend logic)
    print(f"Received data: {data}")

    # Emit a message to the connected clients using SocketIO
    socketio.emit('log', f"Custom event received - Data: {data}")
"""

""" ELK listener"""
def elk_thread(api_key, msg_id, event, max_seconds=60 ):

    """Example of how to send server generated events to clients."""
    count = 0
    current_ts = time.time()
    elk = Elk(host=Config.ELK_HOST, api_key=Config.ELK_SECRET, port=Config.ELK_PORT)
    if not elk.is_connect():
        socketio.emit('response_elk',f"ELK IS NOT CONNECTED !!!, ERROR: {elk.get_errors()}")
        return

    socketio.emit('response_elk', f"Uploading data From ELK for the next {max_seconds} seconds")
    try:
        while event.is_set():
            socketio.sleep(5)
            count += 1
            current_seconds = time.time() - current_ts
            msg_start = f"<span>{count}: Listen {round(current_seconds)} out of {max_seconds} seconds to ELK logs </span>"
            df = elk.query_voange_match_api_and_id(api_key=api_key, msg_id=msg_id)
            log = f"{msg_start} <br> {df.to_html(index=False)}"
            socketio.emit('response_elk', log)

            if current_seconds>max_seconds:
                global thread
                event.clear()
                with thread_lock:
                    if thread is not None:
                        #thread.join()
                        thread = None
    finally:
        event.clear()
        thread = None

if __name__ == '__main__':
    port = int(os.getenv('VCR_PORT', 443))
    current_dir= os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.join(current_dir, 'certs', 'cert.pem')
    key_path  = os.path.join(current_dir, 'certs', 'key.pem')

    socketio.run(app,host="0.0.0.0", port=port, allow_unsafe_werkzeug=True) #  ssl_context=(cert_path, key_path), ssl_context='adhoc'