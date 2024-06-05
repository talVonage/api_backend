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

users_dict = {}

""" Global variables """

""" Return is_connected, _api, msg_conn, api_keys,phone_numbers,apps """
def connect_api ():
    if "key" in session and session["key"] in users_dict:
        msg = f"Connected To Vonage, API Key:{session['key']}"
        api_keys = users_dict[ session["key"] ].subapi
        phone_numbers = users_dict[ session["key"] ].all_numbers
        apps = users_dict[ session["key"] ].apps
        return True, users_dict[ session["key"] ], msg, api_keys, phone_numbers, apps
    else:
        msg = f"Error connecting to Vonage API "
        return False, None, msg, {}, {}, {}

""" Application routes  """
@app.get('/_/health')
async def health():
    return 'OK'

@app.route('/', methods=['GET', 'POST'])
def index():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps  = connect_api ()

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
    #is_form = bool(request.form)
    #if is_form:
    api_key = request.form.get('api_key')
    api_secret = request.form.get('api_sec')

    if api_key and len(api_key) > 0 and api_secret and len(api_secret) > 0:
        session["key"] = api_key
        session["secret"] = api_secret
        _api = Backend_Ui_Api()
        _api.connect_api(api_key=session["key"], api_secret=session["secret"])
        if _api.is_api_connect:
            users_dict[api_key] = _api

    is_connected, _api, msg_conn, api_keys, phone_numbers, apps  = connect_api ()
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
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps  = connect_api ()
    return render_template('sms.html',
                           is_connected=is_connected,
                           msg_conn=msg_conn,
                           msg_dict={})

@app.route('/verify')
def verify():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps  = connect_api ()
    return render_template('verify.html',is_connected=is_connected,
                           msg_conn=msg_conn,
                           msg_dict={})

@app.route('/voice')
def voice():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps  = connect_api ()
    return render_template('voice.html',is_connected=is_connected,
                           msg_conn=msg_conn,
                           msg_dict={})

@app.route('/wa_templates')
def wa_templates():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps  = connect_api ()
    all_templates, all_ex_account, all_msg_apps = {}, [], []

    if is_connected:
        all_ex_account = _api.get_external_account(provider="whatsapp")
        if all_ex_account and len(all_ex_account)>0 and not _api.waba_id:
            _api.waba_id = all_ex_account[-1][1]          #WABA ID FROM LIST OF LISTS
            all_msg_apps = _api.get_application_messages(all_ex_account[-1][0])  #PHONE NUMBER FROM LIST OF LISTS
        else:
            all_msg_apps = _api.get_application_messages()

    all_templates = _api.wa_templates_get()

    return render_template('wa_template.html', all_templates=all_templates,
                           wa_categories=_api.WA_CATEGORIES,
                           wa_lang=_api.WA_LANGUAGES,
                           msg_dict={},
                           all_ex_account=all_ex_account,
                           all_msg_apps=all_msg_apps,
                           is_connected=is_connected,
                           msg_conn=msg_conn)

@app.route('/wa_exec', methods=['POST'])
def wa_exec():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()
    try:
        req = request.get_json()
        template = json.loads(req)
        if template and len(template)>0:
            res = _api.wa_send(template=template)
            return {_api.RESPONSE_SUCCESS:res}
        else:
            return {_api.RESPONSE_FAILED: "Empty template to send "}
    except:
        return {_api.RESPONSE_FAILED: "Error loading template "}

@app.route('/submit_waba', methods=['POST'])
def submit_waba():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()
    waba_id       = request.data.decode('utf-8')
    if waba_id and len(waba_id)>0:
        _api.waba_id = waba_id

    if is_connected:
        all_templates = _api.wa_templates_get()
        msg = {_api.RESPONSE_SUCCESS:f"Using WABA ID {waba_id}", "templates":all_templates}
    else:
        msg = {_api.RESPONSE_FAILED: f"Failed to upload  WABA ID ", "templates": {}}
    return msg

@app.route('/submit_wa', methods=['POST'])
def submit_wa():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()
    selected_name       = request.form.get('wa_combobox')
    selected_component  = request.form.get('json_template')
    selected_lang       = request.form.get('wa_lang')
    selected_category   = request.form.get('wa_category')

    res = _api.wa_update_template(name=selected_name, component=selected_component)
    print (res)

    all_templates = _api.wa_get_templates()

    return render_template('wa_template.html', all_templates=all_templates,
                           wa_categories=_api.WA_CATEGORIES,
                           wa_lang=_api.WA_LANGUAGES,
                           msg_dict=res)

@app.route('/tech')
def tech():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()

    return render_template('tech.html',
                           all_numbers=phone_numbers,
                           msg_dict={},
                           is_connected=is_connected,
                           msg_conn=msg_conn)

@app.route('/tech2')
def tech2():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()
    return render_template('wa_template_javier.html',
                           all_numbers=phone_numbers,
                           msg_dict={},
                           is_connected=is_connected,
                           msg_conn=msg_conn)

@app.route('/tech_reg_validate_number', methods=['POST'])
def tech_reg_number ():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()
    num = request.data.decode('utf-8')
    res = _api.wa_embedded_valid_number(number=num)
    return res

@app.route('/tech_reg_load_numbers', methods=['POST'])
def tech_reg_load_numbers ():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()
    country = request.get_json().get('country')
    numbers = []
    if country and len(country)>0:
        numbers=_api.get_numbers_to_buy (country)
        if numbers and len(numbers)>0:
            numbers = [num[0] for num in numbers]

    return jsonify(numbers)

@app.route('/tech_reg_call_foreword', methods=['POST'])
def tech_reg_call_foreword ():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()
    data = request.get_json()
    from_number = data.get("from")
    to_number = data.get("to")
    res = _api.wa_embedded_call_foreword (from_number, to_number, to_disable=False)
    return res

@app.route('/tech_reg_call_foreword_disabled', methods=['POST'])
def tech_reg_call_foreword_disabled ():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()
    data = request.get_json()
    from_number = data.get("from")
    to_number = data.get("to")
    res = _api.wa_embedded_call_foreword (from_number, to_number, to_disable=True)
    return res

@app.route('/tech_reg', methods=['GET', 'POST'])
def tech_reg ():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()
    wa_code = request.get_json()
    status  = wa_code.get('status')
    resp    = wa_code.get('authResponse')

    ret_json = {"msg": f"WA RESPONSE \n {wa_code}", "id": "", "numbers": []}
    if resp and "code" in resp:
        exchange_code = resp["code"]
        resp = _api.wa_embedded_debug_token (exchange_code=exchange_code)
        ret_json = resp if resp and len(resp)>0 else ret_json

    print (f"SERVER: EMBEDDED SIGN UP RESPONSE: {ret_json}")
    return json.dumps(ret_json)

@app.route('/connect_application', methods=[  'POST'])
def connect_application ():
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()
    uploaded_file = request.files.get('file')
    app_id = request.form.get('text')
    app_name = None
    url_host = request.form.get('url_host')

    all_apps = _api.apps
    for app in all_apps:
        if app[1] == app_id:
            app_name = app[0]
            break

    if uploaded_file:
        file_name = uploaded_file.filename
        if file_name and len(file_name)>0:
            file_content = uploaded_file.read()
            file_content = file_content.decode('utf-8')
            session["app_key"] = app_id
            session["app_secret"] = file_content
            app = _api.connect_app(session=session)
            if app:
                if app_id and app_name and url_host:
                    res = _api.update_application_webhooks(app_id=app_id, app_name=app_name, url_domain=url_host)
                    return {"data": f"Connected to app {app_id}, {res}"}
                return {"data":f"Connected to app {app_id}, Webhooks not configures"}
            else:
                return {"error": f"Error connecting to application"}
    else:
        return {"error":"File is not uploaded... Not connected !"}

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
    print ("** inbound Webhook **")
    data = request.get_json()
    print (data)
    socketio.emit('response_sms', f"INBOUND >>>>  {str(data)} ")
    return ("message_status", 200)

@app.route('/webhooks/status', methods=['POST'])
def sms_status():
    print ("** status Webhook **")
    data = request.get_json()
    print (data)
    socketio.emit('response_sms', f"STATUS >>>>  {str(data)} ")
    return ("message_status", 200)


""" Sockets / Real time events"""
@socketio.on('submit_sms')
def handle_submit(data):
    is_connected, _api, msg_conn, api_keys, phone_numbers, apps = connect_api()
    api_key     = get_not_none (data.get('api_key'),Config.API_KEY)
    api_secret  = get_not_none (data.get('api_sec'), Config.API_SECRET)
    send_from   = data.get('send_from')
    send_to     = data.get('send_to')
    msg         = data.get('msg')
    is_sdk= data.get('is_sdk')

    if is_sdk:
        resp = _api.sms_send_sdk(send_from=send_from, send_to=send_to, msg=msg)
    else:
        resp = _api.sms_send_restapi(send_from=send_from, send_to=send_to, msg=msg)

    logging.info (f"SEND SMS RESPONSE: {resp}")

    # Emit a message to the connected clients using SocketIO
    socketio.emit('response_sms', resp )

    # Add ELK Data
    if _api.msg_id is not None:
        global thread
        with thread_lock:
            if thread is None:
                thread_event.set()
                thread = socketio.start_background_task( elk_thread, api_key, von_api.msg_id, thread_event, 100)

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