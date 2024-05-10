#!/usr/bin/env python3
import os, sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
sys.path.append(os.path.dirname(SCRIPT_DIR))

from  mng_restApi import Rest_Api
from mng_vonage import Vonage
from globals import get_not_none, create_jwt
import logging
from pprint import pprint
import json
from collections import OrderedDict

from config import Config

logger = logging.getLogger(__name__)

class Backend_Ui_Api ():
    WA_CATEGORIES = ['MARKETING','UTILITY','AUTHENTICATION']
    WA_LANGUAGES = {"he":"HEBREW", "en":"ENGLISH"}
    def __init__ (self, api_key=None, api_secret=None, app_id=None, app_secret=None, waba_id=None):
        self._api_key, self._api_secret, self._application_id, self._application_secret, self._waba_id = api_key, api_secret, app_id, app_secret, waba_id
        self._msg_id, self._api = None, None
        self._all_wa_templates = []

        self._api = Vonage()

    def connect (self, api_key=None, api_secret=None, app_id=None, app_secret=None, waba_id=None):
        self._api_key = get_not_none(api_key, self._api_key,  Config.API_KEY)
        self._api_secret = get_not_none(api_secret, self._api_secret, Config.API_SECRET)
        self._application_id = get_not_none(app_id, self._application_id, Config.APPLICATION_KEY)
        self._application_secret = get_not_none(app_secret, self._application_secret, Config.APPLICATION_SECRET)
        self._waba_id = get_not_none(waba_id, self._waba_id, Config.WABA_ID)

        self._api.connect(key=self._api_key, secret=self._api_secret, app_id=self._application_id,
                          app_secret=self._application_secret, waba_id=self._waba_id)

    def is_connect (self):
        return self._api.is_connect()

    def is_connect_application(self):
        return self._api.is_coonect_aaplication()

    @property
    def msg_id(self):
        return self._msg_id

    @property
    def application_id (self):
        return self._api.application_id
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
    @property
    def subapi(self):
        return self._api.all_subapis

    @property
    def all_numbers (self):
        return self._api.all_numbers

    def set_credentials_api  (self, api_key, api_secret):
        self._api.set_api_obj(api_key=api_key, api_secret=api_secret)

    def set_credentials_application  (self, app_id, app_secret):
        self._api.set_app_obj(app_id=app_id, app_secret=app_secret)

    def set_waba  (self, waba_id):
        self._api.set_waba(waba_id=waba_id)

    def send_sms_restapi (self, send_from, send_to, msg):
        self._msg_id = None
        _props = {"from": send_from,
                    "text": msg,
                    "to": send_to,
                    "api_key": self._api_key,
                    "api_secret": self._api_secret}
        _res = self._api.send_sms_restapi(props=_props)
        self._msg_id = self._api.extract_massage_id(res=_res)

        return self._api.get_response(msg_init=f">>> rest_send_sms FROM {send_from} TO {send_to} MSG ID: {self._msg_id}")

    def send_sms_sdk (self, send_from, send_to, msg):
        self._msg_id = None
        _props = {
            'from':send_from,
            'to': send_to,
            'text':msg
        }
        _res = self._api.send_sms_sdk(props=_props)
        self._msg_id = self._api.extract_massage_id(res=_res)

        return self._api.get_response(msg_init=f">>> PYTHON CDK Send SMS FROM {send_from} TO {send_to} MSG ID: {self._msg_id}")

    def wa_get_templates (self, app_id=None, app_secret=None, waba_id=None ):
        self._all_wa_templates =  self._api.wa_get_templates(app_id=app_id, app_secret=app_secret,
                                          waba_id=waba_id, update=True, json_templates=None)

        self._all_wa_templates = self._all_wa_templates if self._all_wa_templates else []
        return self._all_wa_templates

    def wa_update_template (self, name, component):
        if self._all_wa_templates:
            _existing_names = [k for k,v in self._all_wa_templates.items()]
        else:
            _existing_names = []
        _json_comp = json.loads(component)

        res = self._api.wa_update_template(existing_names=_existing_names, name=name, component=_json_comp, app_id=None, app_secret=None, waba_id=None)
        return res

    def get_numbers_to_buy (self, country):
        return self._api.get_number_to_buy (country=country)

"""" REAL TIME FUNCTION """

def test_1 ():
    logging.basicConfig(level=logging.INFO)
    api = Backend_Ui_Api ()

    # res = api.send_sms_sdk(send_from="YOYO123", send_to="447754351600", msg="Hallo world !!")
    res = api.wa_get_templates ( )
    print (res)

def test_2 ():
    res = api.wa_get_templates (
        app_id="bd240d61-98fd-4379-9850-aec8ecd867aa",
        app_secret="/Users/tshany/Documents/gmail_vonage/code/APIs_Keys/private_app_dev.key",
        waba_id="106174865728265",update=True )

    for k,v in res.items():
        print (v['template'])
        print ("-------------------")
        con = api.wa_exec_template (template=v['template'], send_from='447520691600', send_to="447754351600")
        json_res = json.dumps(con, indent=2)
        print (json_res)

#test_1()
