#!/usr/bin/env python3
import os, sys, json, logging
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
sys.path.append(os.path.dirname(SCRIPT_DIR))

from mng_vonage import Vonage
from globals import get_not_none, create_jwt
from config import Config
import phonenumbers
from phonenumbers.phonenumberutil import region_code_for_country_code, region_code_for_number


logger = logging.getLogger(__name__)

class Backend_Ui_Api ():
    WA_CATEGORIES = ['MARKETING','UTILITY','AUTHENTICATION']
    WA_LANGUAGES = {"he":"HEBREW", "en":"ENGLISH"}

    RESPONSE_SUCCESS = 'data'
    RESPONSE_FAILED = 'error'

    def __init__ (self, api_key=None, api_secret=None, app_id=None, app_secret=None, waba_id=None):
        self._api_key, self._api_secret, self._application_id, self._application_secret = api_key, api_secret, app_id, app_secret
        self._msg_id, self._api = None, None
        self._all_wa_templates = []

        self._waba_id = get_not_none(waba_id, Config.WABA_ID)
        self._api = Vonage(waba_id=self._waba_id)


    def connect_api (self,  api_key=None, api_secret=None):
        self._api_key = get_not_none(api_key, self._api_key,  Config.API_KEY)
        self._api_secret = get_not_none(api_secret, self._api_secret, Config.API_SECRET)

        self._api.connect_api(key=self._api_key, secret=self._api_secret)

    def disconnect (self):
        self._api._is_api_connected = False
        self._api._is_app_connected = False
        self._api._vonage = None
        self._api._vonage_app = None

    def connect_app (self, session):
        app_id = session["app_key"] if session and "app_key" in session else None
        app_secret = session["app_secret"] if session and "app_secret" in session else None
        self._application_id = get_not_none(app_id, self._application_id, Config.APPLICATION_KEY)
        self._application_secret = get_not_none(app_secret, self._application_secret, Config.APPLICATION_SECRET)

        if self._application_id and self._application_secret:
            logger.info (f"connect_app -> Successfully connected to application ")
            return self._api.connect_app(app_id=self._application_id, app_secret=self._application_secret)

    @property
    def is_api_connect (self):
        return self._api.is_api_connected

    @property
    def is_app_connect(self):
        return self._api.is_app_connected

    @property
    def msg_id(self):
        return self._msg_id

    @property
    def application_id (self):
        return self._api.application_id

    @property
    def app_key(self):
        return self._api._api_key

    @property
    def apps(self):
        ret = []
        all_apps = self._api.all_apps
        if all_apps and len(all_apps)>0:
            for app_id, app in all_apps.items():
                add_numbers = []
                numbers = app.get("numbers",None)
                if numbers and len(numbers)>0:
                    for number, number_details in numbers.items():
                        add_numbers.append ( [number_details.get("country", ""), number] )
                ret.append ( [app.get("name","Please define !"), app_id, add_numbers , app.get(self._api.APP_CAPABILITIES, [])] )
        return ret

    @property
    def subapi(self):
        return self._api.all_subapis

    @property
    def all_numbers(self):
        return self._api.all_numbers

    @property
    def waba_id(self):
        return self._api.waba_id

    @waba_id.setter
    def waba_id(self, val):
        self._api.waba_id = val

    def apps_by_capabilites (self, capability):
        ret = []
        all_apps = self._api.all_apps
        if all_apps and len(all_apps) > 0:
            for app_id, app in all_apps.items():
                capabilities = app.get(self._api.APP_CAPABILITIES, [])
                app_name = app.get("name", "No Name")
                capabilities_dict = {x.lower():x for x in capabilities}
                if capability.lower() in capabilities_dict:
                    ret.append ([app_id, f"{app_id} | {app_name}"])
        return ret


    def connect_api  (self, api_key, api_secret):
        self._api.connect_api(key=api_key, secret=api_secret)

    def connet_app  (self, app_id, app_secret):
        self._api.connect_app(app_id=app_id, app_secret=app_secret)

    def sms_send_restapi (self, send_from, send_to, msg):
        self._msg_id = None
        _props = {"from": send_from,
                    "text": msg,
                    "to": send_to,
                    "api_key": self._api_key,
                    "api_secret": self._api_secret}
        print ("tal", self._api_secret, self._api_key)
        _res = self._api.sms_send_restapi(props=_props)
        self._msg_id = self._api.massage_extract_id(res=_res)

        return self._api.get_response(msg_init=f">>> rest_send_sms FROM {send_from} TO {send_to} MSG ID: {self._msg_id}")

    def sms_send_sdk (self, send_from, send_to, msg):
        self._msg_id = None
        _props = {
            'from':send_from,
            'to': send_to,
            'text':msg
        }
        _res = self._api.sms_send_sdk(props=_props)
        self._msg_id = self._api.massage_extract_id(res=_res)

        return self._api.get_response(msg_init=f">>> PYTHON CDK Send SMS FROM {send_from} TO {send_to} MSG ID: {self._msg_id}")

    def wa_templates_get (self, waba_id=None, update=True ):
        all_templates = self._api.wa_templates_get( waba_id=waba_id, update=update, wa_templates=None)
        return all_templates if all_templates else {}
    def wa_update_template (self, name, component):
        if self._all_wa_templates:
            _existing_names = [k for k,v in self._all_wa_templates.items()]
        else:
            _existing_names = []
        _json_comp = json.loads(component)

        res = self._api.wa_template_update(existing_names=_existing_names, name=name, component=_json_comp, app_id=None, app_secret=None, waba_id=None)
        return res

    def wa_send (self, template):
        return self._api.messages_send_restapi (template=template)


    def wa_embedded_valid_number (self, number, business_id=None, auth=None):
        auth = auth if auth and len(auth)>0 else Config.WA_EMBEDED_AUTH
        business_id = business_id if business_id and len(business_id)>0 else Config.WA_BUSINESS_ACCOUNT

        if number and auth and business_id:
            return self._api.wa_embeded_valid_number(number=number, auth=auth, business_id=business_id )

    def wa_embedded_debug_token (self, exchange_code, auth=None):
        auth = auth if auth and len(auth) > 0 else Config.WA_EMBEDED_AUTH

        if exchange_code and auth:
            res = self._api.wa_embedded_debug_token(exchange_code=exchange_code, auth=auth )
            logger.info (f"TAL2: backend_ui_api -> wa_embedded_debug_token, res: {res}")
            return res

    def wa_embedded_call_foreword (self, from_number, to_number, to_disable=False):
        res = "Nothing ... "
        country_code = None
        if to_disable:
            to_number = ""
            pn = phonenumbers.parse(f"+{from_number}")
            country_code = region_code_for_country_code(pn.country_code)
        elif to_number and len(to_number)>0 and from_number and len(from_number)>0:
            pn = phonenumbers.parse(f'+{to_number}')
            country_code = region_code_for_country_code(pn.country_code)

        if country_code:
            res = self._api.numbers_update_call_forwards(country=country_code, from_number=from_number, to_number=to_number)
        return res

    def get_numbers_to_buy (self, country):
        return self._api.get_number_to_buy (country=country)

    """Return [ [PHONE_NUMBER, WABA_ID, ACCOUNT_NAME] .. ] """
    def get_external_account (self, provider="whatsapp"):
        ret = []
        _external_account =  self._api.external_accounts_get (provider=provider)
        if _external_account:
            for acc in _external_account:
                ret .append ([acc.get('external_id'), acc.get('aggregate_id'),acc.get('name') ])
        return ret

    def get_application_messages (self, phone_number=None):
        ret = []
        for app in self.apps:
            if 'messages' in app[3]:
                if phone_number and phone_number in app[2]:
                    ret.insert(0, [app[1], f"{app[0]} ({app[1]}), number: {phone_number}"])
                else:
                    ret.append ([app[1], f"{app[0]} ({app[1]}), numbers: {app[2]}"])
        return ret