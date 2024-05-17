"""
GLOBAL FUNCTION
"""

import os, socket, jwt
from time import time
from uuid import uuid4
import base64


""" Return the first not null value from list of arguments """
def get_not_none(*args):
    for arg in args:
        if arg is not None:
            if isinstance(arg, (list, dict, str, tuple)):
                if len(arg) > 0:
                    return arg
            else:
                return arg

""" Check if there is network access to specific URL"""
def ping_url(url, port=None ):
    cmd = f"ping -c 1 {url}"

    if not port:
        is_open = os.system(cmd) == 0

        if not is_open:
            print (f"ping_url failed: {cmd}")
            return False


    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        is_open = sock.connect_ex((url, int(port))) == 0
        if is_open:
            sock.shutdown(socket.SHUT_RDWR)
    except Exception:
        is_open = False
    sock.close()
    print (f"Checked using socket. url:{url}, port:{port}, connected: {is_open}")
    return is_open


def create_jwt (app_id, app_secret_file=None, app_secret_str=None, expires_hours=None):
    algorithm = 'RS256'
    if app_secret_file:
        if not os.path.isfile(app_secret_file):
            print (f"SECRET FILE PATH {app_secret_file} IS NOT EXISTS ")
            return
        with open(app_secret_file, 'r') as file:
            app_secret =  file.read().strip()
    elif app_secret_str:
        algorithm = 'HS256'
        app_secret = app_secret_str
    else:
        print (f"MUST DECLARE app_secret_file or app_secret_str to load secret key")
        return

    iat = int(time())
    payload = {
        "application_id": app_id,
        "iat":iat,
        "jti":str(uuid4())
    }

    if expires_hours:
        payload["exp"] = iat + (expires_hours * 60)

    headers = {'alg': algorithm, 'typ': 'JWT'}
    token = jwt.encode(payload, app_secret, algorithm=algorithm, headers=headers)
    token_str = f"Bearer {token}"

    print ("---------------     TOKEN       ----------------------")
    print (token_str)
    print("---------------     TOKEN       ----------------------")
    return token_str

def create_base64 (key, secret):
    if key and len(key)>0 and secret and len(secret)>0:
        s = f"{key}:{secret}"
        s_bytes = s.encode("ascii")
        # base64_string = base64_bytes.decode("ascii")
        return base64.b64encode(s_bytes)



def test_1():
    create_jwt (app_key="bd240d61-98fd-4379-9850-aec8ecd867aa",
                app_secret_file="/Users/tshany/Documents/gmail_vonage/code/APIs_Keys/private_app_dev.key",
                expires_hours=None)

    create_jwt (app_key="292e6c87",
                app_secret_str="e2IN2xM3Amwx0Ktg",
                expires_hours=None)

def test_2 (key, secret):
    k = create_base64(key, secret)
    print (k)

# Create JWT: vonage jwt --key_file=/Users/tshany/Documents/gmail_vonage/code/APIs_Keys/private_app_dev.key --app_id=bd240d61-98fd-4379-9850-aec8ecd867aa
#test_2 (key="292e6c87", secret="e2IN2xM3Amwx0Ktg")