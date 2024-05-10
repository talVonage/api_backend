import collections
import logging
from functools import reduce
import operator
from collections import OrderedDict
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
import pandas as pd
import os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from my_tools.globals import ping_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
    Host : "nexmo-nlb.kibana.vonagenetworks.net"
    api_key : 'bmVtSXQ0b0J0NkxReVBQU0R3Njc6WkFjYkh1SS1SWEtZb2hXTVBHd01wQQ=='
"""




dict_columns = {"ts": "@timestamp",
                "datacenter": "datacenter",
                "product": "d.product",
                "oa": "d.oa"}

class Elk ():

    FILTER_DAY      = "d"
    FILTER_HOUR     = "h"
    FILTER_MINUTE   = "m"
    FILTER_BY_API   ="api_key"
    FILTER_BY_NUMBER="number"
    FILTER_BY_MSG   ="message_id"
    FILTER_BY_TOPIC ="topic"

    QUERY_MUST          = 'must'
    QUERY_SHOULD        = 'should'
    QUERY_FILTER        = 'filter'
    QUERY_LIST = [QUERY_SHOULD, QUERY_MUST, QUERY_FILTER]

    TOPIC_WSG_OUTBOUND = "event_chatapp_mt"

    topics = {
        "event_hub_all-mt":"SMS",
        "event_hub_all-mo": "SMS",
        "Final-state": "SMS",
        "event_verify_verifiy":"VERIFY",
        "event_quota_activity":"BILLING",
        "event_chatapp_dr":"messages-api-delivery-receipts ",
        TOPIC_WSG_OUTBOUND:"messages-api-msg-terminated-outbound",
        "event_chatapp_mo":"messages-api-msg-originated-inbound",
        "event_sip_rejected":"",
        "event_sip_outbound":""

    }

    SHOULD_FILTER_TYPE = {
        FILTER_BY_API: ["d.acc"],
        FILTER_BY_NUMBER: ["d.oa","d.da","d.from","d.to"],
        FILTER_BY_MSG:["d.id","d.messageId", "d.correlationId", "d.superHubMsgId"],
        FILTER_BY_TOPIC:["topic"]
    }

    GLOBAL_COLUMNS = OrderedDict({
            "@timestamp": "timestamp",
            "d.acc": "api_key_acc",
            "d.oa": "from_oa",
            "d.da": "to_da",
            "d.final": "final",
            "d.status": "status",
            "d.success": "success",
            "d.delivered": "delivered",
            "d.reason": "reason",
            "d.reasonDesc": "reasonDesc",
            "d.product": "product",
            "d.service":"service",
            "d.productPath":"productPath",
            "d.productClass": "productClass",
            "d.country": "country",
            "d.messageId":"messageId",
            "d.Id": "Id",
            "d.msgType":"msgType",
            "d.masterAcc": "masterAcc",
            "d.msg.msg_value": "msg.msg_value",
            "topic": "topic",
            "d.delta": "amount",
            "d.balanceBefore": "balance",
            "d.ref": "reference_id",
            "d.networkName": "networkName",
            "d.net": "net",
            "d.content": "content",
            "d.appId": "appId",
            "d.cost": "cost",
            "d.from": "from",
            "d.to": "to",
            "d.brand": "brand",
            "d.number": "number",
            "d.channel": "channel",
            "d.errorCode": "errorCode",
            "d.internalPrice":"internalPrice",
            "d.rejectedDate":"rejectedDate",
            "d.deliveredDate":"deliveredDate",
            "d.contentType":"contentType",
            "d.route":"route",
            "d.contentAttributes.amCategory":"contentAttributes",
            "d.correlationId":"correlationId",
            "d.gwErrorCode":"gwErrorCode",
            "d.gw":"provider_gw",
            "d.udrType":"udrType",
            "d.superHubMsgId:":"superHubMsgId",
            "d.gw":"gw_gateway"
        })

    COLUMNS_MESSAGES_SMS     = {
            "@timestamp": "time_stamp",
            "d.acc": "API_Key",
            "topic": "topic",
            "d.oa": "oa",
            "d.da": "da",
            "d.product": "product",
            "d.productPath": "productPath",
            "d.productClass": "productClass",
            "d.success": "success",
            "d.final": "final",
            "d.status": "status",
            "d.reason": "reason",
            "d.delivered":"delivered",
            "d.reasonDesc":"reasonDesc",
            "d.service":"service",
            "d.messageId":"messageId",
            "d.networkName":"networkName",
            "d.msgType":"msgType",
            "d.masterAcc": "masterAcc",
            "d.msg.msg_value": "msg_value",
            "d.content":"content",
            "d.country": "Country",
            "d.appId":"appId",
            "d.cost":"cost",
            "d.from":"from",
            "d.to":"to",
            "d.brand":"brand",
            "d.number":"number",
            "d.channel":"channel"
        },

    COLUMNS_VERIFY = OrderedDict({
        "@timestamp": "timestamp",
        "d.acc": "api_key_acc",
        "d.oa": "from_oa",
        "d.da": "to_da",
        "d.final": "final",
        "d.status": "status",
        "d.reason": "reason",
        "d.product": "product",
        "d.productPath": "productPath",
        "d.productClass":"productClass",
        "d.country": "country",
        "d.messageId": "messageId",
        "d.msgType": "msgType",
        "d.masterAcc": "masterAcc",
        "d.msg.msg_value": "msg.msg_value",
        "topic": "topic",
        "d.errorCode":"errorCode"
    }),

    COLUMNS_USAGE   =  OrderedDict({
            "@timestamp": "time_stamp",
            "d.acc": "API_Key",
            "topic": "topic",
            "d.delta":"amount",
            "d.balanceBefore":"balance",
            "d.ref":"reference_id"
        })

    def __init__ (self, host, api_key, port=443, verify_certs=True, timeout=3000):
        if ping_url(host, port):
            # es = Elasticsearch('https://nexmo.kibana.vonagenetworks.net:8443/', basic_auth=('tshany', 'Emily3316!'))
            self.es = Elasticsearch([{"scheme": "https", 'host': host, 'port': int(port)}],
                           api_key=(api_key), verify_certs=verify_certs, request_timeout=timeout)

            logger.info (f"Elastic search connected : {self.es.ping()}")
            # print(es.info())
            print ("ELK Logged in successfully ")
        else:
            self.es = None
            logger.error (f"Network error connecting to {host}:{port}")
            print ("FAILED TO LOG INTO ELK ")

        self._query = None

    def is_connect (self):
        return self.es is not None

    def query_clear (self):
        self._query = None

    def query_builder (self, prop=None, new=False, filter=None):
        if new or not self._query:
            self._query = {"query": {"bool": {"must":[]}  } }

        if prop and len(prop)>0:
            self._query["query"]["bool"]["must"].append (prop)

        if filter and len(filter)>0:
            self._query["query"]["bool"]["filter"]=filter

        return self._query

    def to_df (self, values, cols=[], sort=None):
        if values and len(values)>0:
            row0 = values[0]
            if len (row0) > len(cols):
                for i in range(len (cols), len(row0)):
                    cols.append (f"COL_{i + 1}")
        df = pd.DataFrame(values, columns=cols)

        if sort:
            if not isinstance(sort, (list,tuple)):
                sort = [sort]
            df.sort_values(by=sort, ascending=True)
        return df

    def df_to_cv (self,df, file, index=False):
        df.to_csv(file, index=index ) #encoding='utf-8'
        logger.info(f"ADD FILE {file}")

    def scan_to_cv (self,   file_path, query=None, columns=None, scroll='1m', index='logstash-*',
                            raise_on_error=True, preserve_order=False, clear_scroll=True,
                            add_columns=False, time_column="@timestamp"):
        df = self.scan_to_df (  query=query, columns=columns, scroll=scroll, index=index,
                                raise_on_error=raise_on_error, preserve_order=preserve_order,
                                clear_scroll=clear_scroll, add_columns=add_columns,time_column=time_column )

        if df is not None and not df.empty:
            self.df_to_cv(df, file_path)

        print (f"Return total of {len(df.axes[0])} rows, {len(df.axes[0])} columns")
        return df

    def scan_to_df (self, query=None, scroll='1m', index='logstash-*',
                      raise_on_error=True, preserve_order=False,
                    clear_scroll=True, time_column="@timestamp",columns=None, add_columns=False):

        if not self.es:
            logger.error ("scan_to_df: elastic search is not defined")
            return

        query = query if query else self._query

        # Scan function to get all the data.
        res = scan(client=self.es, query=query,  index=index,
                   raise_on_error=raise_on_error, preserve_order=preserve_order,
                   clear_scroll=clear_scroll,
                   request_timeout=30, size=5000) #scroll=scroll,

        if res is None:
            logger.error (f"Could not find any results, query : {str(query)}")
            return
        else:
            logger.info (f"SCAN DONE!!!!! ")

        output_all = collections.deque()
        output_all.extend(res)
        df = pd.json_normalize(output_all)
        if df is None or df.empty:
            logger.error (f"DATA FRAME IS EMPTY - No record found !!")
            return

        df.columns = df.columns.str.replace("_source.", "")
        nan_value = float("NaN")
        df.replace("", nan_value, inplace=True)
        df.dropna(how='all', axis=1, inplace=True)

        if columns and len (columns)>0:
            columns_dict = dict(columns)
            df.rename(columns=columns_dict, inplace=True)
            filter_col_names= list(columns.values())
            df_columns      = df.columns.values.tolist()
            new_columns     = []
            remain_columns  = []

            for col in df_columns:
                if col in filter_col_names:
                    new_columns.append (col)
                else:
                    remain_columns.append (col)

            logger.info (f"Columns used: {filter_col_names}")
            logger.info(f"Columns remain: {remain_columns}")

            if add_columns:
                new_columns.extend(remain_columns)
            df =  df [ new_columns ]

        if time_column:
            if columns and time_column in columns:
                time_column = columns[time_column]

            if time_column in df.columns:
                df[time_column] = pd.to_datetime(df[time_column])
                df['YEAR'] = df[time_column].dt.year
                df['MONTH'] = df[time_column].dt.month
                df['DAY'] = df[time_column].dt.day
                df['HOUR'] = df[time_column].dt.hour

        df['cnt_int'] = 1

        cols_name = [col for col in df.columns]
        logger.info(f"RETURN TOTAL {len(df.index)} ROWS, {len(cols_name)} COLUMNS ")

        return df

    def f_vonage_should (self, should_filter_type,  props):
        if not should_filter_type or not props:
            return

        should_filter = self.SHOULD_FILTER_TYPE.get(should_filter_type)
        if not should_filter:
            logger.error (f"f_vonage_should: Got {should_filter_type}, Available option are: {self.SHOULD_FILTER_TYPE.keys()}")
            return

        ret = {"bool" : {"minimum_should_match": 1, "should":[]}}
        if props and len(props)>0:
            for prop in props:
                for filter in should_filter:
                    ret["bool"]["should"].append({"match_phrase":{filter:prop}})
        return ret

    def f_vonage_must (self, must_filter, props):
        ret = []
        for prop in props:
            ret.append({"match": {must_filter: prop} })
        return ret

    def f_time_last (self, date_column='@timestamp', intervals=1, to_intervals=None, time_frame=FILTER_DAY  ):
        lt = f"now-{to_intervals}{time_frame}/{time_frame}" if to_intervals else "now"
        gte= f"now-{intervals}{time_frame}/{time_frame}"
        ret =   {"range" :
                    {date_column :
                        {"gte" : gte,
                         "lt" :  lt}
                    }
                }
        return ret

    def query_voange_match_api_and_id (self, api_key, msg_id, log_type="SMS" ):
        # query: The elasticsearch query.
        query = {
            "query":
                {   "bool":{
                    "must": [   {"match": {"d.acc": api_key} },
                                {"match": {"d.id":msg_id} }]
                    }
                }
            }
        return self.scan_to_list(query=query, log_type=log_type)

    def query_vonage (  self, should_dict=None, must_dict=None,
                        folder=None, start_back_legs=1, to_back_legs=None,
                        time_frame=FILTER_DAY, columns=None,add_columns=False, time_column="@timestamp"):
        time_frame = self.f_time_last(date_column=time_column, intervals=start_back_legs,
                                      to_intervals=to_back_legs, time_frame=time_frame)
        should_props = []
        must_props   = []
        if should_dict and len(should_dict)>0:
            for should_filter_type, should_items in should_dict.items():
                should_list = self._get_list(should_items)
                should_props.append (self.f_vonage_should(should_filter_type=should_filter_type, props=should_list))
        if must_props and len(must_dict)>0:
            for must_filter, must_items in must_dict.items():
                must_list = self._get_list(must_items)
                must_props.append (self.f_vonage_must(must_filter=must_filter, props=must_list))


        self.query_clear()
        for should_prop in should_props:
            self.query_builder( should_prop )
        for must_prop in must_props:
            self.query_builder( must_props )
        self.query_builder( filter=time_frame )
        logger.info (f"QUERY USAGE : {self._query}")
        file_name = f"query_{should_filter_type}_interval_{start_back_legs}.csv"
        file_path = os.path.join(folder, file_name) if folder else file_name
        res = self.scan_to_cv (file_path, scroll='1m', index='logstash-*',
                        raise_on_error=True, preserve_order=False, clear_scroll=True,
                        columns=columns, add_columns=add_columns, time_column=time_column)
        return res

    def query_vonage_number (self, numbers, folder=None, start_back_legs=1, to_back_legs=None,
                            time_frame=FILTER_DAY, add_columns=False, time_column="@timestamp" ):
        time_frame = self.f_time_last(date_column=time_column, intervals=start_back_legs,
                                      to_intervals=to_back_legs, time_frame=time_frame)
        apis_list = self._get_list(numbers)
        api_keys = self.f_vonage_apis_keys(apis_list=apis_list)
        if apis_list and len(api_keys) > 0:
            self.query_clear()
            self.query_builder(api_keys)
            self.query_builder(time_frame)
            logger.info(f"QUERY USAGE : {self._query}")
            file_name = f"{apis_list[0]}_time_frame_interval_{start_back_legs}.csv"
            file_path = os.path.join(folder, file_name) if folder else file_name
            res = self.scan_to_cv(file_path, columns=self.COLUMNS_USAGE, scroll='1m', index='logstash-*',
                                  raise_on_error=True, preserve_order=False, clear_scroll=True, add_columns=add_columns,
                                  time_column=time_column)
            return res



    def _get_list (self, prop):
        if prop is not None and isinstance(prop, str):
            prop = prop.replace("|", ",")
            prop = prop.split(",")
            prop = [x.replace(" ","") for x in prop]
            print (f"Convert to list: props: {prop}")
        return prop

    """ Test function - not in use"""
    def __get_val_from_dict (self, dict_data, list_keys, default=None):
        if not isinstance(list_keys , (tuple,list)):
            list_keys = list_keys.split (".")

        try:
            return reduce(operator.getitem, list_keys, dict_data)
        except:
            return default

def test():
    elk = Elk (host='nexmo-nlb.kibana.vonagenetworks.net', port=443,
               api_key='bmVtSXQ0b0J0NkxReVBQU0R3Njc6WkFjYkh1SS1SWEtZb2hXTVBHd01wQQ==')
    pd = elk.get_by_api_key_and_id(api_key="292e6c87", msg_id="cda05809-5b1d-42be-98d8-6b2a29dcbf7f")
    print (pd)
# test()

def get_services ():
    elk = Elk(host='nexmo-nlb.kibana.vonagenetworks.net',
              api_key='bmVtSXQ0b0J0NkxReVBQU0R3Njc6WkFjYkh1SS1SWEtZb2hXTVBHd01wQQ==')
    #pd = elk.get_by_api_key_and_id(api_key="292e6c87", msg_id="cda05809-5b1d-42be-98d8-6b2a29dcbf7f")
    #x = elk.query_vonage_should (should_filter_type=elk.FILTER_BY_API,
    #                             props="f4e39cc6",
    #                             folder="data", start_back_legs=10, to_back_legs=4,
    #                             time_frame=elk.FILTER_DAY, all_columns=True)

    res = elk.query_vonage (should_filter_type=elk.FILTER_BY_NUMBER,
                          should=["447754351600"],  # "972532381137",
                          #must_dict={"d.id":"d5f6018c-8c85-425d-a636-0191c911a14d"},
                          folder="data", start_back_legs=10, to_back_legs=None,
                          time_frame=elk.FILTER_DAY, all_columns=True)
    print ("RESULT ------")



#get_services ()