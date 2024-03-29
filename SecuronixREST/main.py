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

ACTION = ActionParam("ACTION", description="Action to take",
                               input_type=InputType.SELECT, options=["Mark as concern and create incident","Non-Concern","Mark in progress (still investigating)"], 
                               default="Non-Concern", action=["take_inc_action","take_violation_action"])      

ENTITY_TYPE = ActionParam("ENTITY_TYPE", description="Action to take",
                               input_type=InputType.SELECT, options=["Users", "Activityaccount", "RGActivityaccount", "Resources", "Activityip"], 
                               default="Activityaccount", action="take_violation_action")      
                    
        
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


@action(name="Add Comment to Incident")
def add_inc_comment(inc_id: JinjaTemplatedStr, comment: JinjaTemplatedStr):
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


@action(name="take an action on a violation")
def take_violation_action(policyName, resourceGroup, accountName, resourceName, comment: JinjaTemplatedStr):
    """
    This action will add a comment into the Incident
    :param policyName: Policy Name or Violation Name.
    :param resourceGroup: Resource Group Name or Datasource Name
    :param accountName: Entity Name or accountName
    :param resourceName: ResourceName
    :param comment: the comment to be appended to the incident
    :return:
    """
    
    query_params = {
        "tenantname":TENANT.read(),
        "violationName": policyName,
        "datasourceName": resourceGroup,
        "entityType": ENTITY_TYPE.read(),
        "entityName": accountName,
        "actionName": ACTION.read(),
        "resourceName":resourceName,
        "comment": comment
    }

    response = http_request("POST", "/ws/incident/actions", params=query_params)
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'result' in response:
        return response            
        

@action(name="Take Action on an Incident")
def take_inc_action(inc_id: JinjaTemplatedStr):
    """
    This action will add a comment into the Incident
    :param inc_id: The Incident ID with Jinja format.
    :return:
    """
    response = http_request("POST", "/ws/incident/actions?incidentId="+inc_id+'&actionName='+urllib.parse.urlencode(ACTION.read()))
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'result' in response:
        return response     
        

@action(name="Top Violators")
def top_violators(days: JinjaTemplatedStr,max: JinjaTemplatedStr):
    """
    This action will retrieve top N violators
    :param days: Last X days, a number.
    :param max: Max records to return
    :return:
    """
    response = http_request("GET", "/ws/sccWidget/getTopViolators?dateunit=days&dateunitvalue="+days+"&offset=0&max="+max)
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'Response' in response:
        return response["Response"]["Docs"]     


@action(name="Top Violations")
def top_violations(days: JinjaTemplatedStr,max: JinjaTemplatedStr):
    """
    This action will retrieve top N violations
    :param days: Last X days, a number.
    :param max: Max records to return
    :return:
    """
    response = http_request("GET", "/ws/sccWidget/getTopViolations?dateunit=days&dateunitvalue="+days+"&offset=0&max="+max)
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'Response' in response:
        return response["Response"]["Docs"]     

@action(name="Top Threats")
def top_threats(days: JinjaTemplatedStr,max: JinjaTemplatedStr):
    """
    This action will retrieve top N threats
    :param days: Last X days, a number.
    :param max: Max records to return
    :return:
    """
    response = http_request("GET", "/ws/sccWidget/getTopThreats?dateunit=days&dateunitvalue="+days+"&offset=0&max="+max)
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'Response' in response:
        return response["Response"]["Docs"]     
        

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
