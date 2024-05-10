import logging
from api_backend.backend.my_tools.mng_vonage import Vonage
from api_backend.backend.my_tools.config import Config as conf

logging.basicConfig(level=logging.INFO)

vonage = Vonage (key=conf.VON_KEY, secret=conf.VON_SECRET)

# hello world !
def test_vonage_app ():
    vonage.get_balance()
    app1= vonage.get_apps()

def test_api ():
    x = vonage.api_sms_send (to='447754351600', sender ='Vonage', msg='yoyo')
    print (x)

x = vonage.api_whatsup_send  (to='972524417562', sender ='14157386102', msg='XXXXXX dsdsdsd dsdsdsdsd')
print (x)






