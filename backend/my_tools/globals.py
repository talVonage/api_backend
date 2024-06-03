"""
GLOBAL FUNCTION
"""

import os, socket, jwt, re
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


def create_jwt (app_id, app_secret, expires_hours=None):
    if isinstance(app_secret, (str, bytes)) and re.search("[.][a-zA-Z0-9_]+$", app_secret):
        with open(app_secret, "rb") as key_file:
            app_secret = key_file.read()
    elif isinstance(app_secret, str) and '-----BEGIN PRIVATE KEY-----' not in app_secret:
        print("If passing the private key directly as a string, it must be formatted correctly with newlines.")

    algorithm = 'RS256'
    # algorithm = 'HS256'


    iat = int(time())
    payload = {
        "application_id": app_id,
        "iat":iat,
        "jti":str(uuid4())
    }

    if expires_hours:
        payload["exp"] = iat + (expires_hours * 60)
    else:
        iat + (15 * 60)

    payload['exp']  = expires_hours

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