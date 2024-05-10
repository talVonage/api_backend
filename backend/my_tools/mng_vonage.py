import json
from datetime import datetime

import vonage
import logging
from pprint import pformat
from collections import OrderedDict

from mng_restApi import Rest_Api
from globals import create_jwt

logger = logging.getLogger(__name__)
class Vonage ():
    RESPONSE_SUCCESS = 'data'
    RESPONSE_FAILED = 'error'
    RESPONSE_METHOD = 'method'

    """ Used for get_apps dictionary """
    APP_NAME    = 'name'
    APP_NUMBERS = 'numbers'
    APP_CAPABILITIES = 'capabilities'
    NUM_MSISDN  = 'msisdn'
    NUM_FETURES = 'features'
    NUM_COUNTRY = 'country'
    METHOD_SDK = [f"USING PYTHON SDK: ", "import vonage"]
    METHOD_API = [f"USING REST API"]

    TYPE_TEXT       = "text"
    TYPE_IMAGE      = "image"
    TYPE_AUDIO      = "audio"
    TYPE_VIDEO      = "video"
    TYPE_FILE       = "file"
    TYPE_STICKER    = "sticker"
    TYPE_TEMPLATE   = "template"
    TYPE_CUSTOM     = "custom"

    def __init__ (self, key=None, secret=None, app_id=None, app_secret=None, waba_id=None):
        self._api_key, self._api_secret, self._app_id, self._app_secret, self._waba_id = None,None,None,None,None
        self._vonage    = None              # Vonage APIs object
        self._vonage_app= None              # Vonage application
        self._is_ok     = None              # Boolean checking request validation
        self._response = {}                 # Response dictionary {'data':"...", 'error':"....",'method':"..."
        self._wa_all_templates      = None  # Existing whatsapp templates
        self._verify_request_id     = None  # USED FOR VERIFY RESPONSE (Is Verified )
        self._total_phone_numbers   = None  # TOTAL PHONE NUMBERS FOR APP KEY
        self._print_method_str      = None  # List of string descibe the use method (for nice printing )

        self._all_apps, self._all_subapi, self._all_numbers, self._vonage_app = {}, {}, {}, {}
        self.connect(key=key, secret=secret, app_id=app_id, app_secret=app_secret, waba_id=waba_id)

    def connect (self, key, secret, app_id=None, app_secret=None, waba_id=None):
        self._api_key = key if key and len(key)>0 else self._api_key
        self._api_secret = secret if secret and len(secret)>0 else self._api_secret
        self._app_id = app_id if app_id and len(app_id)>0 else self._app_id
        self._app_secret = app_secret if app_secret and len(app_secret)>0 else self._app_secret
        self._waba_id = waba_id if waba_id and len(waba_id)>0 else self._waba_id
        self._vonage = self.set_api_obj(api_key=self._api_key, api_secret=self._api_secret)

        if self.is_connect():
            logger.info ("Connected successfully !!")
            self._all_apps = self._get_vonage_apps_cdk()
            self._all_subapi = self._get_vonage_subapis_cdk()
            self._all_numbers = self._get_vonage_numbers_cdk()
            self._vonage_app = self.set_app_obj(app_id=self._app_id, app_secret=self._app_secret)

    def is_connect (self):
        if not self._vonage:
            logger.error (f"Could not connect to Vonage API")
            return False
        return True

    def is_coonect_aaplication (self):
        if not self._app_secret or not self._app_id:
            return False
        if not self._vonage:
            logger.error (f"Could not connect to Vonage API")
            return False
        return True

    def get_balance_cdk (self):
        if not self.is_connect(): return
        _balance = self._vonage.account.get_balance()
        print(f"Account balance is: {_balance}")
        return _balance

    def get_number_to_buy (self, country):
        if not self.is_connect(): return
        _ret = []
        try:
            _res = self._vonage.numbers.get_available_numbers(country)
            _ret = self._numbers_to_list (_res)
            logger.info(f"Available phone numbers for country {country} is {_res}")

        except Exception as e:
            logger.error(f"Error receiving available number for country  {country}")
            logger.error(e)
        return _ret

    def set_api_obj(self, api_key, api_secret):
        self._api_key   = api_key if api_key else self._api_key
        self._api_secret= api_secret if api_secret else self._api_secret

        if self._api_key and self._api_secret:
            self._vonage = vonage.Client(key=self._api_key, secret=self._api_secret)
        return self._vonage

    def set_app_obj(self, app_id, app_secret):
        self._app_id = app_id if app_id is not None else self._app_id
        self._app_secret = app_secret if app_secret is None else self._app_secret
        self._vonage_app = None

        if self._app_id and self._app_secret:
            self._vonage_app = vonage.Client(application_id=self._app_id, private_key=self._app_secret)
        return self._vonage_app


    def set_waba(self, waba_id):
        self._waba_id = waba_id if waba_id is not None else self._waba_id
        return self._waba_id

    def send_sms_restapi (self, props,  **args):
        url = 'https://rest.nexmo.com/sms/json'
        props_must = ["from", "text", "to", "api_key", "api_secret"]
        _props = self._validate_props(props_dict=props, props_must=props_must, props_additional=None, **args)
        if not _props:
            return

        url_sms = Rest_Api(url=url, content_type=Rest_Api.CONTENT_TYPE_STR)
        res = url_sms.post(data=_props)
        self._is_ok = url_sms.is_ok

        if url_sms.is_ok:
            return res
        else:
            self._set_response(res, self.RESPONSE_FAILED)

        self._set_response(self.METHOD_API.copy(), self.RESPONSE_METHOD)
        self._set_response(f"USING URL {url}, data: {_props}", self.RESPONSE_METHOD)

    def send_sms_sdk (self, props=None, props_valid=None,  **args):
        self._is_ok = False
        props_must = ['from','to','text']

        _props = self._validate_props(props_dict=props, props_must=props_must, props_additional=props_valid, **args)
        if not _props:
            return

        try:
            res = self._vonage.sms.send_message(_props)
            self._is_ok=True
            return res
        except Exception as err:
            self._set_response("Error using CDK", self.RESPONSE_FAILED)
            self._set_response(err, self.RESPONSE_FAILED)

        self._set_response(self.METHOD_SDK.copy(), self.RESPONSE_METHOD)
        self._set_response(f"Methods Properties : {str(_props)}", self.RESPONSE_METHOD)
        self._set_response(f"vonage.sms.send_message({str(_props)})", self.RESPONSE_METHOD)

    def send_messages_sdk (self, props=None, props_valid=None,app_id=None, app_secret=None,  **args):
        self._is_ok = False
        props_must = ['channel', 'message_type', 'to', 'from']
        _props = self._validate_props(props_dict=props, props_must=props_must, props_additional=props_valid, **args)
        _app = self.set_app_obj(app_id=app_id, app_secret=app_secret)
        if not _props or not _app:
            return

        self._method = self.METHOD_SDK.copy()
        try:
            _res = _app.messages.send_message(_props)
            logger.info (_res)
            self._is_ok = True
            return _res
        except Exception as err:
            self._set_response("Error using SDK", self.RESPONSE_FAILED)
            self._set_response(err, self.RESPONSE_FAILED)

        self._method.append(f"Props dictionary: {str(_props)}")
        self._method.append(f"vonage.messages.send_message({str(_props)})")
        return _res

    def extract_massage_id(self, res, msg_id="message-id", node_name='messages', msg_error='error-text'):
        m_id = None
        logger.info(f"extract_massage_id ::: PARSE RESPONSE: {res}")
        messages = res.get(node_name) if node_name else res
        if messages:
            for msg in messages:
                self._set_response("RESPONSE:", self.RESPONSE_SUCCESS)
                if msg_error in msg:
                    self._set_response(msg, self.RESPONSE_FAILED)
                else:
                    m_id = msg.get(msg_id)
                    self._set_response(msg, self.RESPONSE_SUCCESS)
        else:
            self._set_response("No messages found ! ", self.RESPONSE_FAILED)
            self._set_response(res, self.RESPONSE_FAILED)
        return m_id

    def wa_get_templates(self, app_id=None, app_secret=None, waba_id=None, update=True, json_templates=None):
        self._is_ok = False
        _app_id = app_id if app_id else self._app_id
        _app_secret = app_secret if app_secret else self._app_secret
        _waba_id = waba_id if waba_id else self._waba_id

        if not update and self._wa_all_templates is not None:
            return self._wa_all_templates

        if not _waba_id:
            logger.error (f"MUST PROVIDE WABA ! ")
            return

        self._wa_all_templates = OrderedDict({})

        url = f"https://api.nexmo.com/v2/whatsapp-manager/wabas/{_waba_id}/templates"
        if not json_templates:
            try:
                self._method = self.METHOD_API.copy()
                self._method.append(f"USING CURL: {url}")

                _url_template = Rest_Api(url=url)
                token = create_jwt(app_id=_app_id, app_secret_file=_app_secret, app_secret_str=None, expires_hours=None)
                _url_template.set_header('Authorization', token)
                json_templates = _url_template.get()
                logger.info (f"WA templates: {json_templates}")
                self._is_ok = True

            except Exception as err:
                self._set_response(f"Error loading WA templates: {err}", self.RESPONSE_FAILED)
                return

        templates_list = json_templates.get("templates")

        if templates_list and len( templates_list ) > 0:
            for template in templates_list:
                _t_name = template.get("name")
                _t_components = template.get("components")
                _t_lang = template.get("language")
                _t_id = template.get("id")
                _t_category = template.get("category")
                _t_status = template.get("status")
                _t_exec = self.wa_exec_template(template, send_from="", send_to="")

                if _t_name and _t_id:
                    self._wa_all_templates[_t_name] = {"template": template,
                                                  "lang": _t_lang, "category": _t_category, "status": _t_status,
                                                  "exec": _t_exec}
        return self._wa_all_templates

    """ SET Template """
    def wa_exec_template(self, template, send_from, send_to):
        _props = OrderedDict({
            "from": send_from,
            "to": send_to,
            "channel": "whatsapp",
            "message_type": "custom",
            "custom": {
                "type": "template",
                "template": {}
            }
        })

        _props["custom"]["template"] = OrderedDict({
            "name": template.get('name'),
            "language": {
                "policy": "deterministic",
                "code": template.get('language')
            }
        })

        template_component = template.get('components')
        for component in template_component:
            if "example" in component:
                _comp_dict = OrderedDict({
                    "type": component.get("type"),
                    "parameters": []
                })

                _sample_key = list(component["example"].keys())[0]
                _sample_values = component["example"][_sample_key]
                _parameters = []

                if "format" in component:
                    if component["format"].lower() == "image":
                        _url_link = _sample_values[0] if isinstance(_sample_values, list) else _sample_values
                        _parameter = {
                            "type": component["format"].lower(),
                            component["format"].lower(): {
                                "link": _url_link
                            }
                        }
                    else:
                        _parameter = {
                            component["format"]: {
                                "url": _sample_values[0],
                            }
                        }
                    _parameters.append(_parameter)
                else:
                    _sample_values = [_sample_values] if not isinstance(_sample_values, (list, tuple)) else _sample_values
                    _sample_values = _sample_values[0] if isinstance(_sample_values[0], (list, tuple)) else _sample_values
                    for val in _sample_values:
                        _parameters.append({"type": "text", "text": val})

                _comp_dict["parameters"] = _parameters

                if "components" not in _props["custom"]["template"]:
                    _props["custom"]["template"]["components"] = []
                _props["custom"]["template"]["components"].append(_comp_dict)

        return _props

    def wa_update_template (self,existing_names, name,component, app_id=None, app_secret=None, waba_id=None):
        response= {}
        _app_id = app_id if app_id else self._app_id
        _app_secret = app_secret if app_secret else self._app_secret
        _waba_id = waba_id if waba_id else self._waba_id

        all_names = []
        if existing_names and len(existing_names)>0:
            all_names = [x.lower() for x in existing_names]

        # UPDATE TEMPLATE !
        if name.lower() in all_names:
            _t_id = component.get("id")
            if not _t_id:
                response = {self.RESPONSE_FAILED:f"WA UPDATE - Cannot find template ID"}
                logger.error (f"WA UPDATE - Cannot find template ID")
                logger.error(component)
                return response
            else:
                try:
                    url = f"https://api.nexmo.com/v2/whatsapp-manager/wabas/{_waba_id}/templates/{_t_id}"
                    _url_template = Rest_Api(url=url)
                    token = create_jwt(app_id=_app_id, app_secret_file=_app_secret, app_secret_str=None, expires_hours=None)
                    _url_template.set_header('Authorization', token)
                    resp = _url_template.put(data=component)
                    response={self.RESPONSE_SUCCESS:resp}
                    logger.info(f"WA create template response: {resp}")
                except Exception as err:
                    response = {self.RESPONSE_FAILED: f"Error Update WA template: {err}"}

        # Create new template
        else:
            url = f"https://api.nexmo.com/v2/whatsapp-manager/wabas/{_waba_id}/templates"
            component['name'] = name
            component.pop("id", None)       # Remove ID
            component.pop("status", None)   # Remove ID
            try:

                _url_template = Rest_Api(url=url)
                token = create_jwt(app_id=_app_id, app_secret_file=_app_secret, app_secret_str=None, expires_hours=None)
                _url_template.set_header('Authorization', token)

                resp = _url_template.post(data=component)
                response = {self.RESPONSE_SUCCESS: resp}
                logger.info (f"WA create template response: {resp}")
            except Exception as err:
                response = {self.RESPONSE_FAILED: f"Error creating WA templates: {err}"}

        return response

    def get_response(self, msg_init=None):
        ret = {}
        if self.RESPONSE_FAILED in self._response:
            ret[self.RESPONSE_FAILED] = f"ERROR: &#13;&#10; {self._response[self.RESPONSE_FAILED]}"
        elif self.RESPONSE_SUCCESS in self._response:
            msg = f"{msg_init}<br>{self._response[self.RESPONSE_SUCCESS]}" if msg_init else self._response[self.RESPONSE_SUCCESS]
            if self.RESPONSE_METHOD in self._response:
                msg += f"<br><span>METHOD :<br>{self._response[self.RESPONSE_METHOD]}<span>"
            ret[self.RESPONSE_SUCCESS] = msg
        else:
            ret[self.RESPONSE_FAILED] = f"ERROR: There is no massage to display !"
        self._response = {}
        return ret

    """ INTERNAL HELP FUNCTIONS """
    def _validate_props (self, props_dict, props_must=None,props_additional=None, **args):
        _props_dict = props_dict if props_dict else {}
        if args:
            _props_dict = {**_props_dict, **args}

        if props_must and len(props_must)>0 and props_additional and len(props_additional)>0:
            all_props= list(set().union(props_must, props_additional))
        else:
            all_props=props_must if props_must and len(props_must)>0 else props_additional and len(props_additional) if props_additional else None

        if len(_props_dict)<1:
            logger.error (f"Must provide at least one property")
            return False
        _props = {k.lower(): v for k, v in _props_dict.items()}

        if all_props:
            validate_props = [all_props] if not isinstance(all_props, (list,tuple)) else all_props
            if all(prop.lower() in _props for prop in validate_props):
                return _props
            else:
                logger.error(f"Property validation failed, must have {validate_props}, existing properties: {_props.keys()}")
                return False
        return _props

    def _set_response_text (self, msg, msg_type):
        def my_dict_print(d, indent=1):
            h_new_row = "&#13;&#10;"
            h_tab = "&Tab;"
            h_space='&nbsp;'
            if not isinstance(d, (dict, OrderedDict)):
                return d
            ret = "{"+h_new_row
            ind = h_tab * indent
            for k, v in d.items():
                if isinstance(v, (dict, OrderedDict)):
                    ret += f"{ind}{k} : {my_dict_print(v, indent + 1)}"
                else:
                    ret += f"{ind}{k} : {v}{h_new_row}"
            ret += ind + "}"+h_new_row

            return ret

        if msg_type not in self._response:
            self._response[msg_type] = ""

    def _set_response(self, msg, msg_type=RESPONSE_FAILED):
        def my_dict_print(d, indent=0):
            ind = '&nbsp;' * indent
            ret = ind + "{<br>"
            ind = '&nbsp;' * (indent + 4)
            for k, v in d.items():
                if isinstance(v, dict):
                    ret += f"{ind}{k} : {my_dict_print(v, indent + 4)}"
                else:
                    ret += f"{ind}{k} : {v}<br>"
            ret += ind + "}<br>"

            return ret

        if msg_type not in self._response:
            self._response[msg_type] = ""

        if isinstance(msg, (list, tuple)):
            for m in msg:
                self._set_response(str(m), msg_type=msg_type)

        elif isinstance(msg, (dict)):
            self._response[msg_type] += my_dict_print(msg, indent=0)
        else:
            self._response[msg_type] += f"{str(msg)} \n" if msg_type == self.RESPONSE_FAILED else f"<span>{str(msg)}<span><br>"

    """ PROPERTIES """
    @property
    def all_apps (self):
        return self._all_apps

    @property
    def all_subapis (self):
        return self._all_subapi

    @property
    def all_numbers(self):
        return self._all_numbers

    @property
    def application_id(self):
        return self._app_id

    """PRIVATE METHODS  """
    def _get_vonage_apps_cdk(self, max_phones=100):
        if not self.is_connect(): return
        _ret = None
        try:
            _all_apps = self._vonage.application.list_applications()["_embedded"]["applications"]
            if _all_apps and len(_all_apps) > 0:
                _ret = {}
                for app in _all_apps:
                    app_id = app['id']
                    _ret[app_id] = { self.APP_NAME: app['name'],
                                        self.APP_NUMBERS: {},
                                        self.APP_CAPABILITIES: []
                                        }
                    all_capabilites = app.get(self.APP_CAPABILITIES)
                    if all_capabilites and len(all_capabilites)>0:
                        for cap in all_capabilites:
                            _ret[app_id][self.APP_CAPABILITIES].append (cap)

            account_numbers = self._vonage.numbers.get_account_numbers(size=max_phones)

            numbers = account_numbers.get('numbers')
            self._total_phone_numbers = account_numbers.get('count')

            if numbers and len(numbers) > 0:
                for number in numbers:
                    app_id = number.get('app_id')
                    country = number.get('country')
                    msisdn = number.get('msisdn')
                    features = number.get('features')

                    if app_id and msisdn:
                        if app_id not in _ret:
                            _ret[app_id] = {self.APP_NUMBERS: {}}
                        _ret[app_id][self.APP_NUMBERS][msisdn] = {self.NUM_MSISDN: msisdn,
                                                                  self.NUM_COUNTRY: country,
                                                                  self.NUM_FETURES: features}
        except Exception as e:
            logger.error(f"Error loading existing application for API Key {self._api_key}")
            logger.error(e)

        return _ret

    def _get_vonage_subapis_cdk(self):
        if not self.is_connect(): return
        _api_dict = None
        _ret = {}
        try:
            _res = self._vonage.subaccounts.list_subaccounts()
            _accounts = _res.get('_embedded')
            if _accounts and len(_accounts)>0:
                _p_acc = _accounts.get('primary_account')
                _s_acc = _accounts.get('subaccounts')
                if _p_acc:
                    _p_acc = _p_acc.get('api_key')
                    _api_dict = {_p_acc:_s_acc}

            if _api_dict and len(_api_dict)>0:
                for api, sub_api_list in _api_dict.items():
                    for sub_api in sub_api_list:
                        sub_api_key = sub_api.get("api_key")
                        sub_api_name = sub_api.get("name")
                        sub_api_create = sub_api.get("created_at")
                        api_key = sub_api.get("primary_account_api_key")
                        if api_key and len(api_key)>0 and api_key not in _ret:
                            _ret[api_key] = []

                        if sub_api_create and len(sub_api_create) > 0:
                            sub_api_create = datetime.strptime(sub_api_create, "%Y-%m-%dT%H:%M:%S.000Z")
                            sub_api_create = sub_api_create.strftime("%d-%m-%y")
                        _ret[api_key].append ([sub_api_key, sub_api_name, sub_api_create])



            logger.info(f"Sub API::: {_ret}")

        except Exception as e:
            logger.error(f"Error loading SUB APIs for API Key {self._api_key}")
            logger.error(e)

        return _ret

    def _get_vonage_numbers_cdk (self):
        if not self.is_connect(): return []
        _ret = []
        try:
            _res = self._vonage.numbers.get_account_numbers()
            _ret = self._numbers_to_list (_res)
            logger.info(f"Phone numbers for API Key {self._api_key} is {_res}")

        except Exception as e:
            logger.error(f"Error receiving numbers for API Key {self._api_key}")
            logger.error(e)
        return _ret

    def _numbers_to_list (self, res):
        ret = []
        if res and len(res)>0:
            all_numbers = res.get("numbers")
            if all_numbers and len(all_numbers) > 0:
                for number in all_numbers:
                    num_country = number.get("country")
                    num_msisdn = number.get("msisdn")
                    num_feature = number.get("features")
                    ret.append([num_msisdn, num_country, num_feature])
        return ret
    """"   OLD VERSION :::: --------------------------------------------------------------------"""

    def send_fb_msg (self, to, sender, msg):
        res = self.api_msg(channel="messenger", message_type='text', to=to, sender=sender, text=msg)
        logger.info(f"send_fb_msg: >> {res} ")
        return res

        FB_RECIPIENT_ID = '6795968170432721'
        VONAGE_FB_SENDER_ID = '100614398987044'  # '107083064136738'

        res = self.client_app.messages.send_message(
            {
                "channel": "messenger",
                "message_type": "text",
                "to": FB_RECIPIENT_ID,
                "from": VONAGE_FB_SENDER_ID,
                "text": "This is a Facebook Messenger text message sent using the Vonage Messages API",
            }
        )

        print (res)

    def varify_send_sms (self, phone_num="447754351600"):
        verify = vonage.Verify(self.client_key)

        response = verify.start_verification(number=phone_num, brand="AcmeInc")
        if response["status"] == "0":
            self.varify_req_id = response["request_id"]
            print("Started verification request_id is %s" % ( self.varify_req_id ))
        else:
            self.varify_req_id = None
            print("Error: %s" % response["error_text"])

    def varify_is_ok (self):
        if self.varify_req_id:
            pass

    def varify2_start (self, phone_number='447754351600', brand='yoyo'):
        request_id = None
        params = {  'brand': brand,
                    'workflow': [
                        {'channel': 'sms', 'to': phone_number}],
        }

        try:
            req = self.client_app.verify2.new_request(params)
            if 'request_id' in req:
                return req['request_id']
        except vonage.ClientError as error:
            logger.error(error)
        return request_id

    def varify2_cancel (self, request_id):
        try:
            self.client_app.verify2.cancel_verification(request_id)
            return True
        except vonage.ClientError as error:
            logger.error(error)
        return False

    def varify2_test (self, request_id, code):
        try:
            self.client_app.verify2.check_code(request_id=request_id, code=code)
            return True
        except vonage.ClientError as error:
            logger.error(error)
        return False

    def ncco_ask_me_call (self, uuid):
        return [
            {"action": "talk", "text": "How can I help ?", },
            {
                "action": "input",
                "type": ["speech"],
                "eventUrl": [f"{DOMAIN_URL}/webhooks/asr"],
                "speech": {
                    "endOnSilence": 1,
                    "language": "en-US",
                    "uuid": [uuid],
                    # Change to request.json.get("uuid") if using POST-JSON webhook format
                },
            },
            {"action": "talk", "text": "Good bye"},
        ]

    def ncco_record (self):
        return  [
            {
                "action": "talk",
                "text": "recording started  "
            },
            {
                "action": "record",
                # "split": "conversation",
                # "channels": 2,
                "eventUrl": [f"{DOMAIN_URL}/webhooks/recordings?name=fdfdfdfd"],
                "endOnKey": '#',
                "transcription":
                    {
                        "eventMethod": "POST",
                        "eventUrl": [f"{DOMAIN_URL}/webhooks/transcription"],
                        "language": "en-US"
                    }
            },
            {
                "action": "connect",
                "endpoint": [
                    {
                        "type": "app",
                        "user": "Alice"
                    }
                ]
            }
        ]


TO_NUMBER='447754351600'  #  support@api.vonage.com
WHATSAPP_NUMBER='14157386102'
WHATSAPP_TEMPLATE_NAMESPACE='ccccc'
WHATSAPP_TEMPLATE_NAME='xxzxz'

def test_1 ():
    logging.basicConfig(level=logging.INFO)
    from pprint import pprint
    v = Vonage (key=None, secret=None,    #key='292e6c87', secret='e2IN2xM3Amwx0Ktg',
                app_id="bd240d61-98fd-4379-9850-aec8ecd867aa",
                app_secret="/Users/tshany/Documents/gmail_vonage/code/APIs_Keys/private_app_dev.key")
    #v.get_balance()
    #pprint (v.all_apps)
    #pprint (v.all_subapis)
    #v.get_numbers

    r = v.get_number_to_buy (country="IL")
    v.connect(key='292e6c87', secret='e2IN2xM3Amwx0Ktg')
    r = v.get_number_to_buy(country="IL")


def test_2 ():
    props = {
        "channel": "whatsapp",
        "message_type": "template",
        "to": '447754351600',
        "from": "447520691600",  # "447520691600", # 14157386102
        # "text" : "How you doing today !"
        "template": {
            "name": "test_tal:test_tal",  # :{WHATSAPP_TEMPLATE_NAME}
            "parameters": [
                "Tal",
            ],
        },
        "whatsapp": {"policy": "deterministic", "locale": "en"},
    }

    #v.api_messages_send_wa_template(send_from="447520691600", send_to="447754351600",
    #                                template_name="test_tal:test_tal", template_params=["moshe",], locale="en",
    #                                app_id=None, app_secret=None)

    # "447520691600"
    #v.api_messages_send_wa (type=v.TYPE_TEMPLATE, send_from="447520635100", send_to="447754351600",
    #                                   text=None, url=None, caption=None, file_name=None,
    #                                   template_name="test_tal:test_tal", template_params=["Gohn",], custom=None,
    #                                   locale='en',
    #                                   client_ref=None, webhook_url=None, webhook_version=None,
    #                                   app_id=None, app_secret=None)

    url =  "https://storage.googleapis.com/picup-server-sdk-v2-campaigns-images/610/600"

    #rr = v.send_message(channel='whatsapp',   send_from="447520691600", send_to='447754351600',
    #               msg="Hallo world!", msg_type='text')
    #print (rr)

    #res = v.varify2_start(phone_number='447754351600', brand='yoyo')
    ##print (res)
    #res = v.varify2_test (request_id='54df0364-7c8d-4586-b85b-f96fbbd6e45c', code='6281')
    #print(res)
    # ret = v.varify2_cancle('ed9b1d44-4fd5-40ef-ac5f-42a76aeb1a48')
    # print (ret)
    #
    #v.send_whatsup_text (msg_to='972524417562',msg_from='14157386102', msg='Yoyoy here I am !!!')

#test_1 ()


