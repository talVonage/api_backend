from mng_restApi import Rest_Api
from urllib.parse import urljoin

class WhatsApp ():
    def __init__ (self, waba_id, api_version="v15.0"):
        user_access_token = ""
        whatsapp_number =""
        business_id=""
        recipient_number=""
        media_id=""
        media_url=""
        upload_id=""

        self._base_url = f"https://graph.facebook.com/{api_version}/{waba_id}"
        self._rest = Rest_Api(url=self._base_url, content_type=None)


    def create_tamplate (self, name):
        _url = self._rest.set(path=f'/message_templates',query={'name':name} )
        print (_url)

        body = {
            "name": "intro_catalog_offer",
            "language": "en_US",
            "category": "MARKETING",
            "components": [
                {
                    "type": "BODY",
                    "text": "Now shop for your favourite products right here on WhatsApp! Get Rs {{1}} off on all orders above {{2}}Rs! Valid for your first {{3}} orders placed on WhatsApp!",
                    "example": {
                        "body_text": [
                            [
                                "100",
                                "400",
                                "3"
                            ]
                        ]
                    }
                },
                {
                    "type": "FOOTER",
                    "text": "Best grocery deals on WhatsApp!"
                },
                {
                    "type": "BUTTONS",
                    "buttons": [
                        {
                            "type": "CATALOG",
                            "text": "View catalog"
                        }
                    ]
                }
            ]
        }


def tests ():
    w = WhatsApp (waba_id="123456")
    w.create_tamplate(name="test123")

tests ()


