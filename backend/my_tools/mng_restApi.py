import urllib3, json, base64, sys
from codecs import BOM_UTF8
from urllib.parse import urljoin, urlparse, urlunparse, urlencode
import logging
import requests
from collections import OrderedDict
logger = logging.getLogger(__name__)

urllib3.disable_warnings()


class Rest_Api():
    CONTENT_TYPE    = 'Content-Type'
    CONTENT_TYPE_STR     = 'form-urlencoded'

    CONTENT_DICT = {CONTENT_TYPE_STR:'application/x-www-form-urlencoded'}
    def __init__ (self, url, content_type=None):
        self._base_url = url
        self._url = self._base_url
        self._headers= {}

        self._scheme, self._netloc, self._base_path, self._base_params, self._base_query, self._base_fragment = urlparse(self._base_url)
        self.set_header(k=content_type)
        self._is_ok = None

    @property
    def url (self):
        return self._url

    @property
    def is_ok(self):
        return self._is_ok

    def set_header (self, k, v=None):
        if not k or len(k)<1:
            return

        if k == self.CONTENT_TYPE_STR:
            self._headers[self.CONTENT_TYPE] = self.CONTENT_DICT[ self.CONTENT_TYPE_STR ]
        else:
            self._headers[k] = v

    def set(self, path=None, query=None, fragment=None):
        if path and self._base_path:
                path = f"{self._base_path}{urljoin('/',path)}"
        if query and len(query)>0:
            query = f"{self._base_query}&{urlencode(query)}" if self._base_query else urlencode(query)
        fragment=fragment if fragment else self._base_fragment
        self._url= urlunparse((self._scheme, self._netloc, path, self._base_params, query, fragment))
        return self._url

    def put(self, base_url=None, post_url=None, data=None, headers=None, respose_is_json=True):
        return self._send(type="PUT",
                          base_url=base_url,post_url=post_url,
                          data=data,headers=headers,respose_is_json=respose_is_json)

    def get(self, base_url=None, post_url=None, data=None, headers=None, respose_is_json=True):
        return self._send(  type="GET",
                            base_url=base_url, post_url=post_url,
                            data=data, headers=headers, respose_is_json=respose_is_json)

    def post (self, base_url=None, post_url=None, data=None, headers=None, respose_is_json=True):
        return self._send(  type="POST",
                            base_url=base_url, post_url=post_url,
                            data=data, headers=headers, respose_is_json=respose_is_json)

    def delete (self, base_url=None, post_url=None, headers=None):
        return self._send(  type="DELETE",
                            base_url=base_url, post_url=post_url,
                            data=None, headers=headers,respose_is_json=False)

    def _set_data (self, data):
        if not data or len(data)<1:
            return None

        if self._headers and self.CONTENT_TYPE in self._headers:
            if self.CONTENT_DICT.get(self.CONTENT_TYPE_STR, None) == self._headers [self.CONTENT_TYPE]:
                if isinstance(data, dict):
                    return "&".join ([f"{k}={v}"for k,v in data.items()])

        return json.dumps(data).encode('utf-8') if data and len(data) > 0 else None


    def _send (self, type, base_url=None, post_url=None, data=None, headers=None, respose_is_json=True):
        self._is_ok = False
        url = base_url if base_url else self.url
        if headers and len(headers)>0:
            headers.update(self._headers)
        else:
            headers=self._headers
        data = self._set_data (data)

        if post_url:
            post_url="/"+post_url if post_url[0]!="/" else post_url
            url+=post_url

        try:
            if "PUT"==type:
                r = requests.put(url, data=data, headers=headers)
                r_status =  r.status_code
                r_text = r.text
            else:
                http = urllib3.PoolManager(cert_reqs='CERT_NONE')
                r = http.request(type, url, headers=headers, body=data)
                r_status = r.status
                r_text = r.data.decode("utf-8-sig")
                # replace BOM string !
                r_text = r_text.encode("utf-8")  # replace ('\ufeff', "")
            if 200 == r_status:
                if respose_is_json:
                    logger.debug("%s: JSON RESPONSE GET 200>> URL %s" % (type, url))
                    self._is_ok = True
                    return json.loads( r_text, object_pairs_hook=OrderedDict )
                else:
                    logger.debug("%s: STRING RESPONSE GET 200>> URL %s" % (type, url))
                    self._is_ok = True
                    return r.data.decode("utf-8")
            else:
                logger.error("USING METHOD %s: ERROR CODE %s --> MSG: %s" % (type,r_status, r_text))
                if respose_is_json:
                    return json.loads( r_text, object_pairs_hook=OrderedDict )
                else:
                    return r_text

        except urllib3.exceptions.HTTPError as e:
            ret = f"'Request failed: '{e.reason}"
            logger.error('Request failed:', e.reason)
            #raise Exception (e.reason)
            return ret
        except:
            e = sys.exc_info()[0]
            ret = f"_send FAILED, ERROR {e}"
            logger.error (ret)
            #raise Exception (e)
            return ret