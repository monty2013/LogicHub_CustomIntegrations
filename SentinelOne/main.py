"""
name: SentinenOne
description: Pre-release integration concept
logoUrl: https://www.sentinelone.com/wp-content/uploads/2018/04/Logo-400x400.jpg
"""
from lhub_integ import action, connection_validator
from lhub_integ.common import helpers
from lhub_integ.params import ConnectionParam, InputType
import requests
import json

VERSION = "1.0.0"
URL = ConnectionParam("URL", description="API Endpoint")
API_TOKEN = ConnectionParam("API_TOKEN", description="API Token", input_type=InputType.PASSWORD)


@connection_validator
def validate_connections():
    if not URL.read():
        return [ValidationError(message="Parameter must be defined", param=URL)]

    if not API_TOKEN.read():
        return [ValidationError(message="Parameter must be defined", param=API_TOKEN)]

    url = f"{URL.read()}/web/api/v2.1/users/login/by-api-token"

    data = {"data": {
        "apiToken": API_TOKEN.read(),
        "reason": "API Token Validation"
        }}
    try: 
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        return response.raise_for_status()
    except Exception as ex:
        return [ValidationError(message=f"Authentication Failed")]
    

@action(name="List Agents")
def list_agents():
    """
    This action will list the agents
    :return:
    """
    response = http_request("GET", "/web/api/v2.1/agents")
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response.get('data')
        
@action(name="Get System Status")
def get_system_status():
    """
    This action will get system status
    :return:
    """
    response = http_request("GET", "/web/api/v2.1/system/status")
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response.get('data')      
        
@action(name="Get System Info")
def get_system_info():
    """
    This action will get system info
    :return:
    """
    response = http_request("GET", "/web/api/v2.1/system/info")
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response.get('data')              

@action(name="Disconnect Endpoint from Network")
def disconnect_from_network_request(agents_id):
    """
    This action will disconnect the endpoint from the network
    :param agent_id: Agent ID
    :return:
    """
    endpoint_url = '/web/api/v2.1/agents/actions/disconnect'

    payload = {
        'filter': {
            'ids': agents_id
        }
    }
    response = http_request('POST', endpoint_url, data=json.dumps(payload))
    if response.get('errors'):
        return_error(response.get('errors'))
    else:
        return response.get('data',{})


@action(name="Connect Endpoint to Network")
def connect_to_network_request(agents_id):
    """
    This action will enable the endpoint to connect the network
    :param agent_id: Agent ID
    :return:
    """
    endpoint_url = '/web/api/v2.1/agents/actions/connect'

    payload = {
        'filter': {
            'ids': agents_id
        }
    }
    response = http_request('POST', endpoint_url, data=json.dumps(payload))
    if response.get('errors'):
        return_error(response.get('errors'))
    else:
        return response.get('data',{})

@action(name="initiate-scan")
def initiate_scan(agents_id):
    """
    This action start agent scanning
    :param agent_id: Agent ID
    :return:
    """
    endpoint_url = '/web/api/v2.1/agents/actions/initiate-scan'
    payload = {
        'filter': {
            'ids': agents_id
        }
    }
    response = http_request('POST', endpoint_url, data=json.dumps(payload))
    if response.get('errors'):
        return_error(response.get('errors'))
    else:
        return response.get('data',{})
        
@action(name="Fetch Agent Logs")
def fetch_log(agents_id):
    """
    This action fetches agent logs
    :param agent_id: Agent ID
    :return:
    """
    endpoint_url = '/web/api/v2.1/agents/actions/fetch-logs'
    payload = {
        'filter': {
            'ids': agents_id
        }
    }
    response = http_request('POST', endpoint_url, data=json.dumps(payload))
    if response.get('errors'):
        return_error(response.get('errors'))
    else:
        return response.get('data',{})

@action(name="Hash Reputation")
def hash_reputation(hashcode):
    """
    This action will return hash reputation of the input
    :param hashcode: Hash value column
    :return:
    """
    response = http_request("GET", "/web/api/v2.1/hashes/{hashcode}/reputation")
    if response.get('errors'):
        return {"has_error":"true", "error_msg":(response.get('errors'))}
    if 'data' in response:
        return response.get('data',{})

    

def http_request(method, url_suffix, params={}, data=None):
    HEADERS = {
        'Authorization': 'ApiToken ' + API_TOKEN.read(),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    res = requests.request(
        method,
        URL.read() + url_suffix,
        verify=False,
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
                f'Error in API call to Sentinel One [{res.status_code}] - [{res.reason}] \n'
                f'Error details: [{errors}]'
            )
        except Exception:
            raise ValueError(f'Error in API call to Sentinel One [{res.status_code}] - [{res.reason}]')
    try:
        return res.json()
    except ValueError:
        return None    
    
