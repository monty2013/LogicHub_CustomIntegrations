"""
name: Securonix REST Add-on
description: This integration uses Securonix REST API to compliments the OOTB integration. The detail about Securonix REST API can be found at https://documentation.securonix.com/onlinedoc/Content/Cloud/Content/SNYPR%206.3/Web%20Services/6.3_REST%20API%20Categories.htm
logoUrl: https://lhub-public.s3.amazonaws.com/integrations/snypr.jpeg
"""
import requests
import json
import os
from lhub_integ.params import ConnectionParam, ActionParam, InputType, JinjaTemplatedStr
from lhub_integ.common import input_helpers,verify_ssl
from lhub_integ import action
import urllib.parse
import datetime

URL = ConnectionParam("URL", description="API Endpoint, for example, https://a1t8yrhf.securonix.net/Snypr")
USERNAME = ConnectionParam("USERNAME", description="A valid service account username. This user requires Web Service rights via Roles")
PASSWORD = ConnectionParam("PASSWORD", description="Password for the service account.", input_type=InputType.PASSWORD)
TENANT = ConnectionParam("TENANT", description="Tenant Name for a multi-tenant environment")

START_TIME_MS=input_helpers._get_safe_stripped_env_integer('__execution_start_time_ms')
END_TIME_MS=input_helpers._get_safe_stripped_env_integer('__execution_end_time_ms')

RANGE_TYPE = ActionParam("RANGE_TYPE", description="Range Type",
                               input_type=InputType.SELECT, options=["updated",
                                                                     "opened",
                                                                     "closed"], default="updated", action="list_incidents")

        
        
@action(name="Add Comment to Incident")
def add_comment(inc_id: JinjaTemplatedStr, comment: JinjaTemplatedStr):
    """
    This action will add a comment into the Incident
    :param inc_id: The Incident ID with Jinja format.
    :param comment: the comment to be appended to the incident
    :return:
    """
    response = http_request("POST", "/ws/incident/actions?incidentId="+inc_id+'&actionName=comment&comment='+urllib.parse.urlencode(comment))
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'result' in response:
        return response     

        
@action(name="List Incidents")
def list_incidents(query: JinjaTemplatedStr):
    """
    This action will return the Incident Listing based on the range type.
    :param query: additional query parameters can be inserted, not required. For example, status=blah. This is a jinja template field.
    :return:
    """

    response = http_request("GET", "/ws/incident/get?type=list&from="+str(START_TIME_MS)+'&to='+str(END_TIME_MS)+'&rangeType='+RANGE_TYPE.read())
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'result' in response:
        return response["result"]["data"]["incidentItems"]                        


def http_request(method, url_suffix, params={}, data=None):
    token = os.environ.get('TOKEN', 'Not Set')
    HEADERS = {
        "token":str(token)
    }
    res = requests.request("GET", URL.read()+"/ws/token/validate",headers=HEADERS)
    if res.status_code not in {200}:
        HEADERS = {
            "username":USERNAME.read(),
            "password":PASSWORD.read(),
            "tenant":TENANT.read(),
            "validity":"1"
        }
        res = requests.request("GET", URL.read()+"/ws/token/generate",headers=HEADERS)
        if res.status_code not in {200}:
            try: 
                errors = ''
                for error in res.json().get('errors'):
                    errors = '\n' + errors + error.get('detail')
                raise ValueError(
                    f'Error in API call to Securonix [{res.status_code}] - [{res.reason}] \n'
                    f'Error details: [{errors}]'
                )
            except Exception:
                raise ValueError(f'Error in API call to Sentinel One [{res.status_code}] - [{res.reason}]')
        else:
            os.environ['TOKEN'] = res.text
            token = res.text
          
    HEADERS = {
        'token': str(token),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    res = requests.request(
        method,
        URL.read() + url_suffix,
        verify=verify_ssl.verify_ssl_enabled(),
        params=params,
        data=data,
        headers=HEADERS
    )
    if res.status_code not in {200}:
        try:
            errors = ''
            for error in res.json().get('errors'):
                errors = '\n' + errors + error.get('detail')
            raise ValueError(
                f'Error in API call to Securonix [{res.status_code}] - [{res.reason}] \n'
                f'Error details: [{errors}]'
            )
        except Exception:
            raise ValueError(f'Error in API call to Securonix [{res.status_code}] - [{res.reason}]')
    try:
        return res.json()
    except ValueError:
        return None   
