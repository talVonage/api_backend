"""
GLOBAL FUNCTION
"""

import os, socket, jwt
from time import time
from uuid import uuid4


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


def tests():
    create_jwt (app_key="bd240d61-98fd-4379-9850-aec8ecd867aa",
                app_secret_file="/Users/tshany/Documents/gmail_vonage/code/APIs_Keys/private_app_dev.key",
                expires_hours=None)

    create_jwt (app_key="292e6c87",
                app_secret_str="e2IN2xM3Amwx0Ktg",
                expires_hours=None)

    JWT_APP1="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBsaWNhdGlvbl9pZCI6ImJkMjQwZDYxLTk4ZmQtNDM3OS05ODUwLWFlYzhlY2Q4NjdhYSIsImlhdCI6MTcwMDgzODE3MCwianRpIjoiMjAyMy0xMS0yNCAxNTowMjo1MC44MDA0OTAifQ.t--OjMNHHXWTuyh0xgspdUusl7qY9MLDeRpZLABz2ck_oNBKXM898IZWmq9QNhXyc3-9GhC5-NNXtfbpbq9axPcqfL5Gcdf9d-zSM0aO13CF0H2LcrlYrG0k9rAf6yF7RTm5F2iLbR-q-aL5Ert4J-oR_E7N-uOjUB7Wv_pBLuSykph-RZ0e7FlAWFanQoXvKijCKGCH9RpJVB_MKc9T1D5DcOlrE1GAaBE_W3fXbrHur_PiTH0nWkpvH2lJRLQc7DPeu4WhBEZdEvN-WyMAQISnehHaLMUC3ySDWCzlfDSE1OVWtinfn9465ncwY2zIXkkSPTXwQFd9OMkW5n0rog"

    JWT2 = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBsaWNhdGlvbl9pZCI6IjI5MmU2Yzg3IiwiaWF0IjoxNzAxMDkwNTAyLCJqdGkiOiIyMDIzLTExLTI3IDEzOjA4OjIyLjQzODQwNCJ9.InXWX6rkkiuXVal5YPaHZ2XS4KGiiO5L4aKewZ8WW0Y"
    #       Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3MDEwOTE4OTYsImp0aSI6IjQ5N2I3ZmIwLThkMjktMTFlZS1iNzRjLWE1OTkwNGU2NDZlNCIsImFwcGxpY2F0aW9uX2lkIjoiYmQyNDBkNjEtOThmZC00Mzc5LTk4NTAtYWVjOGVjZDg2N2FhIiwiZXhwIjoxNzAxMDkxOTE3NzA3fQ.Q15mC4x-YctYNu1ChU711RriqoQOHhxejpwBWF0ZNHXwJLG9HcFXQo1GBG0uRI-Q0sXXKa0BeoseO-neuNRn7WhiU1rphZJ4XEE9y29L4tfbAZpf9lUoCheZwhEH7KL2fA72JZS0vRbT42Mtr70V0gK1efn4yYffLtAscq7V7RbxuXx_oEflB-z0Tl2GDwjm2hCxBrGsPKmjG0q4swPz860uyD4txdfNYzVKXewaXiSPvZW7scT0Ys4dj3j-uiTbw6tL00NkLY718HrZEMa6IcnYFfoLirXFwvYsCnxa5vyqT3vwvOIJ6bPznWBiHm0eN1Ien7kEXz2DMYEQz0pjAg

    # Create JWT: vonage jwt --key_file=/Users/tshany/Documents/gmail_vonage/code/APIs_Keys/private_app_dev.key --app_id=bd240d61-98fd-4379-9850-aec8ecd867aa