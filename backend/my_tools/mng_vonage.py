import json, os, re
from datetime import datetime
import vonage
import logging
from collections import OrderedDict

from mng_restApi import Rest_Api
from globals import create_jwt, create_base64

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
        self._api_key, self._api_secret, self._app_id, self._app_secret = None,None,None,None
        self._waba_id   = waba_id
        self._vonage    = None              # Vonage APIs object
        self._vonage_app= None              # Vonage application
        self._is_ok     = None              # Boolean checking request validation
        self._is_api_connected = False
        self._is_app_connected = False
        self._response = {}                 # Response dictionary {'data':"...", 'error':"....",'method':"..."
        self._wa_all_templates      = None  # Existing whatsapp templates
        self._verify_request_id     = None  # USED FOR VERIFY RESPONSE (Is Verified )
        self._total_phone_numbers   = None  # TOTAL PHONE NUMBERS FOR APP KEY
        self._print_method_str      = None  # List of string descibe the use method (for nice printing )

        self._all_apps, self._all_subapi, self._all_numbers, self._vonage_app = {}, {}, {}, {}
        self.connect_api(key=key, secret=secret)
        self.connect_app(app_id=app_id, app_secret = app_secret)


    """ ALL PROPERTIES """
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

    @property
    def waba_id(self):
        return self._waba_id

    @waba_id.setter
    def waba_id(self, value):
        self._waba_id = value if value and len(str(value))>0 else None

    @property
    def is_api_connected (self):
        return self._is_api_connected

    @property
    def is_app_connected(self):
        return self._is_app_connected

    def connect_api (self, key=None, secret=None):
        if key and len(key)>0 and secret and len(secret)>0:
            self._vonage = vonage.Client(key=key, secret=secret)
            _balance = self.get_balance ()
            if _balance:
                self._api_key = key
                self._api_secret = secret
                self._api_bearer = create_base64(key=self._api_key, secret=self._api_secret)
                self._api_bearer = f"Basic {self._api_bearer.decode('utf-8')}" if self._api_bearer and len(self._api_bearer)>0 else None
                self._is_api_connected = True
                self._all_apps = self._get_vonage_apps_cdk()
                self._all_subapi = self._get_vonage_subapis_cdk()
                self._all_numbers = self._get_vonage_numbers_cdk()
                logger.info(f"Vonage SDK is connected successfully, Current balance: {_balance}")
                return self._vonage

    def connect_app(self, app_id=None, app_secret=None):
        if app_id and len(app_id) > 0 and app_secret and len(app_secret) > 0:
            try:
                self._vonage_app = vonage.Client(application_id=app_id, private_key=app_secret)

                #TODO: // Check how app is connecteed !
                self._is_app_connected = True
                self._app_id = app_id
                self._app_secret = app_secret
                logger.info(f"Vonage APPLICATION is connected successfully ... ")
            except Exception as e:
                self._is_app_connected = False
                msg = f"Failed application connection: {e}"
                logger.error (msg)
        return self._is_app_connected

    def is_waba_exists (self, waba_id=None):
        _waba_id = waba_id if waba_id and len(waba_id)>0 else self._waba_id
        if not _waba_id or len(str(_waba_id))<1:
            logger.error(f"MUST PROVIDE WABA ID ! ")
            return False

        self.waba_id = _waba_id
        return True

    def get_balance (self):
        if not self._vonage:
            return
        try:
            _balance = self._vonage.account.get_balance()
            print(f"Account balance is: {_balance}")
            return _balance
        except:
            return None

    def get_number_to_buy (self, country):
        if not self.is_api_connected: return
        _ret = []
        try:
            _res = self._vonage.numbers.get_available_numbers(country)
            _ret = self._numbers_to_list (_res)
            logger.info(f"Available phone numbers for country {country} is {_res}")

        except Exception as e:
            logger.error(f"Error receiving available number for country  {country}")
            logger.error(e)
        return _ret

    def sms_send_restapi (self, props,  **args):
        url = 'https://rest.nexmo.com/sms/json'
        props_must = ["from", "text", "to", "api_key", "api_secret"]
        if not args.get("api_key") or len(args.get("api_key"))<1:
            args["api_key"] = self._api_key

        if not args.get("api_secret") or len(args.get("api_secret"))<1:
            args["api_secret"] = self._api_secret

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

    def sms_send_sdk (self, props=None, props_valid=None,  **args):
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

    def messages_send_sdk (self, props=None, props_valid=None,app_id=None, app_secret=None,  **args):
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

    def messages_send_restapi (self, template):
        url = "https://api.nexmo.com/v1/messages"

        if not self.is_app_connected:
            return

        try:
            self._method = self.METHOD_API.copy()
            self._method.append(f"USING CURL: {url}")

            _url = Rest_Api(url=url)
            bearer = self._get_app_jwt()
            _url.set_header('Authorization', bearer)
            res = _url.post(data=template)
            logger.info(f"Message send, response: {res}")
            self._is_ok = True
            return res

        except Exception as err:
            self._set_response(f"Error loading WA templates: {err}", self.RESPONSE_FAILED)
            return

    def massage_extract_id(self, res, msg_id="message-id", node_name='messages', msg_error='error-text'):
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

    def wa_templates_get (self, waba_id=None, update=True, wa_templates=None):
        if not self._is_api_connected or not self._api_bearer:
            logger.error (f"wa_templates_get:-> Not connected to Vonage API")
            return


        if not update and self._wa_all_templates is not None:
            return self._wa_all_templates

        if not self.is_waba_exists(waba_id=waba_id):
            logger.error(f"wa_templates_get:-> WABA not exists ")
            return

        self._is_ok = False
        self._wa_all_templates = OrderedDict({})

        url = f"https://api.nexmo.com/v2/whatsapp-manager/wabas/{self.waba_id}/templates"
        if wa_templates is None :
            try:
                self._method = self.METHOD_API.copy()
                self._method.append(f"USING CURL: {url}")

                _url_template = Rest_Api(url=url)
                _url_template.set_header('Authorization', self._api_bearer)
                wa_templates = _url_template.get()
                logger.info (f"WA templates: {wa_templates}")
                self._is_ok = True

            except Exception as err:
                self._set_response(f"Error loading WA templates: {err}", self.RESPONSE_FAILED)
                return

        templates_list = wa_templates.get("templates")

        if templates_list and len( templates_list ) > 0:
            for template in templates_list:
                _t_name = template.get("name")
                _t_components = template.get("components")
                _t_lang = template.get("language")
                _t_id = template.get("id")
                _t_category = template.get("category")
                _t_status = template.get("status")
                _t_exec = self.wa_template_exec_(template, send_from="", send_to="")

                if _t_name and _t_id:
                    self._wa_all_templates[_t_name] = {"template": template,
                                                  "lang": _t_lang, "category": _t_category, "status": _t_status,
                                                  "exec": _t_exec}
        return self._wa_all_templates

    def wa_template_exec_(self, template, send_from, send_to):
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

    def wa_template_update (self,existing_names, name,component, waba_id=None):
        if not self._is_api_connected or not self._api_bearer: return
        if not self.is_waba_exists(waba_id): return

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
                    url = f"https://api.nexmo.com/v2/whatsapp-manager/wabas/{self.waba_id}/templates/{_t_id}"
                    _url_template = Rest_Api(url=url)
                    _url_template.set_header('Authorization', self._api_bearer)
                    resp = _url_template.put(data=component)
                    response={self.RESPONSE_SUCCESS:resp}
                    logger.info(f"WA create template response: {resp}")
                except Exception as err:
                    response = {self.RESPONSE_FAILED: f"Error Update WA template: {err}"}

        # Create new template
        else:
            url = f"https://api.nexmo.com/v2/whatsapp-manager/wabas/{self.waba_id}/templates"
            component['name'] = name
            component.pop("id", None)       # Remove ID
            component.pop("status", None)   # Remove ID
            try:

                _url_template = Rest_Api(url=url)
                _url_template.set_header('Authorization', self._api_bearer)
                resp = _url_template.post(data=component)
                response = {self.RESPONSE_SUCCESS: resp}
                logger.info (f"WA create template response: {resp}")
            except Exception as err:
                response = {self.RESPONSE_FAILED: f"Error creating WA templates: {err}"}

        return response

    def wa_embeded_valid_number (self, number, auth, business_id, version="v19.0"):
        ret = "No Data"
        if number and len(number)>0 and auth:
            url = f"https://graph.facebook.com/{version}/{business_id}/add_phone_numbers?phone_number={number}"

            try:
                self._method = self.METHOD_API.copy()
                self._method.append(f"USING CURL: {url}")

                _url_add_numbers = Rest_Api(url=url)
                _url_add_numbers.set_header('Authorization', auth)
                msg = _url_add_numbers.post()
                if "error" in msg:
                    err_msg = msg["error"].get("message")
                    if "you do not have permission to access this endpoint" in err_msg.lower():
                        ret = f"Number {number} can be used as whatsapp number"
                    else:
                        ret =  f"Number {number} is not valid for whatsapp"
            except Exception as err:
                self._set_response(f"Error loading WA templates: {err}", self.RESPONSE_FAILED)
        print (ret)
        return ret

    """ MAIN Function: based on exchange_code -> receive shared wabas -> receive waba numbers    
        1. API call to receive token
           self._wa_embedded_debug_token(response) : parsing response. return dictionary with waba id 
           dict_response =  {'msg':<Message to show for users>, 'id':< List of Managed WABA IDs >}
           
        2. API call to receive numbers for manage waba (using the above dict_response ) 
           self.wa_embedded_waba_get_phone_numbers (waba_id... ):  return list with all numbers : [ [num_id, num]... ]
           append into dict_response all numbers 
        return: {'msg':<Message to show for users>, 'id':< List of Managed WABA IDs >, 'numbers':[ [num_id, num ]... ]} 
    """
    def wa_embedded_debug_token (self, exchange_code, auth, version="v19.0"):
        ret = json.dumps ({"msg":"could not connect", "id":"", "numbers":[]})
        url = f"https://graph.facebook.com/{version}/debug_token?input_token={exchange_code}"

        try:
            self._method = self.METHOD_API.copy()
            self._method.append(f"USING CURL: {url}")

            _url_debug = Rest_Api(url=url)
            _url_debug.set_header('Authorization', auth)
            logger.info (f"Exec URL: {url}")
            ret = self._wa_embedded_debug_token (_url_debug.get())

        except Exception as err:
            self._set_response(f"Error loading WA templates: {err}", self.RESPONSE_FAILED)
            return ret


        logger.info (f"wa_embedded_debug_token response: {ret}")
        waba_id = ret.get('id')
        if waba_id and len(waba_id) > 0:
            for waba in waba_id:
                phone_numbers = self.wa_embedded_waba_get_phone_numbers(waba_id=waba, auth=auth)
                ret['numbers'] = phone_numbers

        logger.info (ret)
        return ret

    """ Return: {"msg":<log message>, "id":<managed waba id>}
        parse response:
        {   "data" : {  "app_id" : "670843887433847",
                        "application" : "JaspersMarket",
                        "data_access_expires_at" : 1672092840,
                        "expires_at" : 1665090000,
                        "granular_scopes" : [   {   "scope" : "whatsapp_business_management",
                                                    "target_ids" : [
                                                        "102289599326934", // ID of newest WABA to grant app whatsapp_business_management
                                                        "101569239400667"]
                                                 }, … ]
                        }
        }
 
     """
    def _wa_embedded_debug_token (self, response):
        print(f"TAL1: _wa_embedded_debug_token: {response}")

        ret = {"msg":f"Could not find target IDs in response \n {response}",
               "id":None}

        if response is not None and len(response)>0 and "data" in response:
            ret = {"msg":"Data exists in response"}
            da = response["data"]
            granular_scope = da.get("granular_scopes")
            if granular_scope and len (granular_scope)>0:
                ret['msg'] += "\n granular_scopes in response"
                for scope in granular_scope:
                    scope_name = scope.get("scope")
                    scope_target_ids = scope.get("target_ids")
                    print (f"Found {scope_name} , target IDs: {scope_target_ids}")
                    if scope_name and "whatsapp_business_management" == scope_name:
                        if scope_target_ids and len(scope_target_ids)>0:
                            ret['msg'] += f"\n found target_ids in response {scope_target_ids}"
                            ret['id'] = scope_target_ids[0]

        print (f"TAL1: _wa_embeded_debug_token: {ret}")
        return ret

    """ Return list of lists: [ [number_id, phone number] ... ]
        self._wa_embedded_waba_get_phone_numbers: Parsing response  
    """
    def wa_embedded_waba_get_phone_numbers (self, waba_id, auth, version="v19.0"):
        print (f"TAL2 wa_embedded_waba_get_phone_numbers : WABA: {waba_id} ")
        url = f"https://graph.facebook.com/{version}/{waba_id}/phone_numbers?fields=display_phone_number"

        try:
            _url_debug = Rest_Api(url=url)
            _url_debug.set_header('Authorization', auth)
            ret = self._wa_embedded_waba_get_phone_numbers(_url_debug.get())

        except Exception as err:
            self._set_response(f"Error loading WA templates: {err}", self.RESPONSE_FAILED)
            return

        print(f"TAL2 wa_embedded_waba_get_phone_numbers : response: {ret} ")
        return ret

    """ Parse response format :
    {"data": [
        {   "id": "1972385232742141",    
            "display_phone_number": "+1 631-555-1111" }]
    }
    """
    def _wa_embedded_waba_get_phone_numbers (self, response):
        ret = []
        if response and len(response)>0 and "data" in response:
            for number in response["data"]:
                num_id = number.get("id")
                num_display = number.get("display_phone_number")
                if num_display and len(num_display)>0:
                    num_display = re.sub(r'\D', '', num_display)
                    ret.append ( (num_id, num_display))
        return ret

    def numbers_update_call_forwards (self, country, from_number, to_number, call_back_type="tel"):
        to_number = to_number if to_number and len(to_number) > 0 else ""
        data_dict = {
            "country":country,
            "msisdn":from_number,
            "voiceCallbackValue":to_number,
            "voiceCallbackType":call_back_type
        }
        if not self._is_api_connected or not self._api_bearer:
            logger.error (f"numbers_update_call_forwards:-> Not connected to Vonage API")
            return "Not connected to vonage api"

        url = "https://rest.nexmo.com/number/update"
        try:
            self._method = self.METHOD_API.copy()
            self._method.append(f"USING CURL: {url}")

            _url = Rest_Api(url=url)
            _url.set_header('Authorization', self._api_bearer)
            _url.set_header(k=_url.CONTENT_TYPE_STR)
            res = _url.post(data=data_dict)
            self._is_ok = True
            error_code = res.get('error-code')
            if error_code and error_code == '200':
                if to_number == "":
                    return "Number Forward Is Disabled "
                return f"Number Forward to {to_number} successfully .. "
            else:
                return f"Response: {res}"

        except Exception as err:
            self._set_response(f"Error loading WA templates: {err}", self.RESPONSE_FAILED)
            return f"ERROR: {err}"


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

    def external_accounts_get (self, provider=None):
        ret = []
        if not self._is_api_connected or not self._api_bearer:
            logger.error (f"wa_templates_get:-> Not connected to Vonage API")
            return

        url = f"https://api.nexmo.com/beta/chatapp-accounts/"
        try:
            self._method = self.METHOD_API.copy()
            self._method.append(f"USING CURL: {url}")

            _url_template = Rest_Api(url=url)
            _url_template.set_header('Authorization', self._api_bearer)
            _ex_accounts = _url_template.get()
            _ex_accounts =_ex_accounts.get("_embedded")

            if _ex_accounts and len(_ex_accounts)>0:
                for acc in _ex_accounts:
                    if provider and len(provider)>0:
                        if acc.get("provider","None").lower() == provider.lower():
                            ret.append (acc)
                    else:
                        ret.append(acc)

        except Exception as err:
            self._set_response(f"Error loading external accounts: {err}", self.RESPONSE_FAILED)

        logger.info (f"External accounts: {ret}")
        return ret


    """ INTERNAL HELP FUNCTIONS - PRIVATE METHODS """
    def _get_app_jwt (self, app_id=None, app_secret=None):
        _app_id = app_id if app_id and len(app_id)>0 else self._app_id
        _app_secret = app_secret if app_secret and len(app_secret)>0 else self._app_secret

        if _app_id and _app_secret and self.is_app_connected:
            return  create_jwt(app_id=_app_id, app_secret=_app_secret,expires_hours=None)
        else:
            logger.error (f"Failed to create JWT token for app { _app_id }")

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

    def _get_vonage_apps_cdk(self, max_phones=100):
        if not self.is_api_connected: return
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
        if not self.is_api_connected: return
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
        if not self.is_api_connected: return []
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

    def voice_ncco_ask_me_call (self, uuid):
        DOMAIN_URL = ""
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

    def voice_ncco_record (self):
        DOMAIN_URL = ""
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


