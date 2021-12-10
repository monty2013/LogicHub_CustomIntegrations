"""
name: LogRhythm REST
description: This integration uses LogRhythm REST API to interact with alarms. The detail about LogRhythm REST API can be found at https://docs.logrhythm.com/docs/lrapi/rest-api
logoUrl: https://docs.logrhythm.com/docs/lrapi/_/7F0000010170782D37AE5FDD0C5777E7/1626043713777/Logo.jpg
"""
import requests
import json
from lhub_integ.params import ConnectionParam, ActionParam, InputType, JinjaTemplatedStr
from lhub_integ.common import input_helpers,verify_ssl
from lhub_integ import action
import datetime

URL = ConnectionParam("URL", description="API Endpoint, for example, https://<PM IP Address>:8501. Read more about LogRhythem REST API from https://docs.logrhythm.com/docs/lrapi/rest-api")
API_TOKEN = ConnectionParam("API_TOKEN", description="API Token for 3rd party application. Read more at https://docs.logrhythm.com/docs/lrapi/rest-api/administration-api/register-third-party-applications-to-use-the-admin-api", input_type=InputType.PASSWORD)

START_TIME_MS=input_helpers._get_safe_stripped_env_integer('__execution_start_time_ms')
END_TIME_MS=input_helpers._get_safe_stripped_env_integer('__execution_end_time_ms')


@action(name="Query Alarms")
def query_alarms(query_string: JinjaTemplatedStr):
    """
    This action will return all matched Alarms
    :param query_string: The query string avaialble with Alarm REST call with Jinja format.
    :return:
    """
    response = http_request("GET", "/lr-alarm-api/alarms?{query_string}")
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response
        
@action(name="Get Alarm Detail")
def get_alarm(alarm_id: JinjaTemplatedStr):
    """
    This action will return the Alarm Detail
    :param alarm_id: The alarm ID with Jinja format.
    :return:
    """
    response = http_request("GET", "/lr-alarm-api/alarms/{alarm_id}")
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response
                
@action(name="Update Alarm Status")
def update_status(alarm_id: JinjaTemplatedStr, alarm_status: JinjaTemplatedStr):
    """
    This action will return the Alarm Detail
    :param alarm_id: The alarm ID with Jinja format.
    :param alarm_status: Valid status are: New, Opened, Working, Escalated, Closed, Closed_FalseAlarm, Closed_Resolved, Closed_Unresolved, Closed_Reported, Closed_Monitor, or 0 to 9
    :return:
    """
    payload = {
        "AlarmStatus":alarm_status
    }
    response = http_request("PATCH", "/lr-alarm-api/alarms/{alarm_id}", data=payload)
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response        
        
@action(name="Update Alarm RBP")
def update_rbp(alarm_id: JinjaTemplatedStr, rbp: JinjaTemplatedStr):
    """
    This action will return the Alarm Detail
    :param alarm_id: The alarm ID with Jinja format.
    :param rbp: Valid status are: Risk based priority score
    :return:
    """
    payload = {
        "rBP":rbp
    }
    response = http_request("PATCH", "/lr-alarm-api/alarms/{alarm_id}", data=payload)
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response   
        
@action(name="Add Alarm Comment")
def add_comment(alarm_id: JinjaTemplatedStr, comment: JinjaTemplatedStr):
    """
    This action will return the Alarm Detail
    :param alarm_id: The alarm ID with Jinja format.
    :param comment: Valid status are: New, Opened, Working, Escalated, Closed, Closed_FalseAlarm, Closed_Resolved, Closed_Unresolved, Closed_Reported, Closed_Monitor, or 0 to 9
    :return:
    """
    payload = {
        "alarmComment":comment
    }
    response = http_request("POST", "/lr-alarm-api/alarms/{alarm_id}/comment", data=payload)
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response     
        
@action(name="Get Alarm Events")
def get_alarm_event(alarm_id: JinjaTemplatedStr):
    """
    This action will return the Alarm Detail
    :param alarm_id: The alarm ID with Jinja format.
    :return:
    """
    response = http_request("GET", "/lr-alarm-api/alarms/{alarm_id}/events")
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response        
        
@action(name="Get Threat Intelligence")
def get_intel(ioc: JinjaTemplatedStr):
    """
    This action will return the IOC intelligence detail
    :param ioc: IOC either passed as column or as fixed data. This is a jinja template field.
    :return:
    """
    payload = {
        "vaule":ioc
    }
    response = http_request("POST", "/Observables/actions/search", data=payload)
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response                        

@action(name="Test Connectivity")
def test(host_id: JinjaTemplatedStr):
    """
    This action will try to retrive host lr-admin-api/hosts/your_host_id
    :param host_id: The host ID with Jinja format, for example, 1 
    :return:
    """
    response = http_request("GET", "/lr-admin-api/hosts/{host_id}")
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response    

def http_request(method, url_suffix, params={}, data=None):
    HEADERS = {
        'Authorization': 'Bearer ' + API_TOKEN.read(),
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
                f'Error in API call to LogRhythm [{res.status_code}] - [{res.reason}] \n'
                f'Error details: [{errors}]'
            )
        except Exception:
            raise ValueError(f'Error in API call to LogRhythm [{res.status_code}] - [{res.reason}]')
    try:
        return res.json()
    except ValueError:
        return None   
