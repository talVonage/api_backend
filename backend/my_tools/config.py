"""Flask config."""
from os import environ, path
from dotenv import load_dotenv

BASE_DIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASE_DIR, "../.env"))

APP_SECRET= 'appsecret'
APP_KEY   = "appkey"
class Config:

    API_KEY = environ.get("API_KEY")
    API_SECRET = environ.get("API_SECRET")

    APPLICATION_KEY = environ.get("APPLICATION_KEY")
    APPLICATION_SECRET=environ.get("APPLICATION_SECRET")
    WABA_ID=environ.get("WABA_ID")
    WA_EMBEDED_AUTH = environ.get("WA_EMBEDED_AUTH")
    WA_BUSINESS_ACCOUNT = environ.get("WA_BUSINESS_ACCOUNT")

    DICT_APPS = {"DEV":{APP_KEY:"bd240d61-98fd-4379-9850-aec8ecd867aa",
                       APP_SECRET:"/Users/tshany/Documents/gmail_vonage/code/APIs_Keys/private_app_dev.key"}
                }

    ELK_HOST    = environ.get("ELK_HOST")
    ELK_PORT    = environ.get("ELK_PORT")
    ELK_SECRET = environ.get("ELK_SECRET")



    VON_NUMBER = ""

    """ OLD CONFIGURATION     
    # Flask configuration variables
    # General Config
    FLASK_APP           = environ.get("FLASK_APP")
    FLASK_ENV           = environ.get("FLASK_ENV")
    SECRET_KEY          = environ.get("SECRET_KEY")
    SECURITY_PASSWORD_SALT= environ.get("SECURITY_PASSWORD_SALT")


    # Static Assets
    STATIC_FOLDER       = "static"
    TEMPLATES_FOLDER    = "templates"

    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI         = environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_ECHO                 = False
    SQLALCHEMY_TRACK_MODIFICATIONS  = False

    MAIL_SERVER         = environ.get('MAIL_SERVER')
    MAIL_PORT           = environ.get('MAIL_PORT')
    MAIL_USERNAME       = environ.get('MAIL_USERNAME')
    MAIL_PASSWORD       = environ.get('MAIL_PASSWORD')
    MAIL_USE_TLS        = False
    MAIL_USE_SSL        = True
    MAIL_DEFAULT_SENDER = environ.get('MAIL_DEFAULT_SENDER')
    
    """