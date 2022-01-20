"""
name: MISP - Opensource
description: This is a community provided integration for users to use as is and open source. Since this integration does not implement all of MISPs endpoints, the real API reference guide is at https://www.misp-project.org/documentation/openapi.html
logoUrl: https://s3.amazonaws.com/lhub-public/integrations/misp-logo.png
"""
import requests
import time
import json
from lhub_integ.params import ConnectionParam, ActionParam, InputType, JinjaTemplatedStr, DataType, ValidationError
from lhub_integ.common import input_helpers, file_manager_client, validations, verify_ssl
from lhub_integ import action, connection_validator
import datetime

URL = ConnectionParam("URL",
                      description="This is the API endpoint with API version. For example, https://your_misp_svr.domain.local",
                      input_type=InputType.TEXT)
API_TOKEN = ConnectionParam("API_TOKEN",
                            description="This is the API Authorization Token",
                            input_type=InputType.PASSWORD)
MINIMAL = ActionParam("MINIMAL", description="Fetch for minimal data. The default is True", data_type=DataType.BOOL, optional=True,
                               input_type=InputType.SELECT, default="True",options= ["True", "False"],
                               action=["recent_event","all_events"])
PUBLISHED = ActionParam("PUBLISHED", description="Search for Published? The default is True", data_type=DataType.BOOL, optional=True,
                               input_type=InputType.SELECT, default="True",options= ["True", "False"],
                               action="event_search")                               
CATEGORY = ActionParam("CATEGORY", description="event category",
                               optional=True,
                               input_type=InputType.SELECT, options= ["Internal reference","Targeting data","Antivirus detection",
                                    "Payload delivery","Artifacts dropped","Payload installation","Persistence mechanism","Network activity",
                                    "Payload type","Attribution","External analysis","Financial fraud","Support Tool","Social network","Person","Other"],
                               default=None, action="event_search")   
THREAT_LEVEL = ActionParam("THREAT_LEVEL", description="Threat level where 1 is high, 2 is medium, 3 is low, and 4 is undefined",
                               optional=True,default=None,
                               input_type=InputType.SELECT,options= ["1","2","3","4"],
                               action=["event_search","add_event"])   
DISTRIBUTION = ActionParam("DISTRIBUTION", description="Who will be able to see this event once it becomes published: 0=your organization, 1=this community, 2=connected community, 3=all communities, 4=sharing group, 5=inherit event",
                               optional=True,
                               input_type=InputType.SELECT,options= ["0","1","2","3","4","5"],default=None,
                               action="add_event")                                  
ANALYSIS = ActionParam("ANALYSIS", description="Analysis Maturity Level: 0=Initial, 1=Ongoing, 2=Complete",
                               optional=True,
                               input_type=InputType.SELECT,options= ["0","1","2"],default=None,
                                action="add_event")                                   

@connection_validator
def validate_connections():
    if not URL.read():
        return [ValidationError(message="API Endpoint must be defined", param=URL)]
    if not API_TOKEN.read():
        return [ValidationError(message="API Authorization Token must be defined", param=API_TOKEN)]
    url = f"{URL.read()}/events/index"
    # Just need to set a dummy payload for the search to return 200 status so the API token is validated
    payload = {"limit":1, "minimal":True, "searchDatefrom":"2029-01-23"}
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json','Accept': 'application/json', 'Authorization': API_TOKEN.read()}, data=json.dumps(payload))
        return response.raise_for_status()
    except Exception as ex:
        return [ValidationError(message=f"Authentication Failed")]


@action(name="Last X Events")
def recent_event(X):
    """
    Retrieves the most recent X number of events
    :param X: The last X number of events. If no column there, you can do "=5" to pass the value through.
    :return:
    """
    params = {}
    params["sort"] = "timestamp"
    params["direction"] = "desc"
    params["minimal"] = MINIMAL.read()
    i = 0
    try:
        i = int(X)
    except ValueError:
        return {"has_error": True, "message":"X is not a number"}
    except Exception:
        return {"has_error": True, "message":"error converting X into number"}
    response = http_request("POST", "/events/index", data=json.dumps(params))
    return response[:i]


@action(name="Search Events")
def event_search(value, value_type, last, org, event_id, tags):
    """
    Search for events with filters. With many options to either search for or filter by.
    :param value: String to search for, eg, ="127.9.0.1" or ="Malicious" or some hashcodes
    :optional value: True
    :param value_type: one of the many types that carries values, eg, ="md5", "sha256", "filename", "url", "ip-src", etc. Too long to list, please use reference: https://www.misp-project.org/documentation/openapi.html#tag/Events
    :optional value_type: True
    :param last: published in the last X amount of time, eg, ="1d" or ="12h" or ="30m", default is 1d if not defined.
    :optional last: True
    :param org: org name, eg: ="LogicHub"
    :optional org: True
    :param event_id: optional event_id, eg, ="3279" where 3279 is the event_id
    :optional event_id: 
    :param tags: an comma separated string, eg: "tlp:amber","Type:OSINT"
    :optional tags: True
    :return:
    """
    req = {"page": 0, "limit": 1, "returnFormat":"json"}
    if value:
        req["value"] = value
    if value_type:
        req["type"] = value_type
    if last :
        req["last"] = last
    else :
        req["last"] = "1d"
    if org:
        req["org"] = org
    if event_id:
        req["eventid"]=event_id
    if tags:
        req["tags"]=[tags]
    if PUBLISHED.read():
        req['published'] = PUBLISHED.read()        
    if CATEGORY.read():
        req['category'] = CATEGORY.read()
    if THREAT_LEVEL.read():
        req['threat_level_id'] = THREAT_LEVEL.read()
    print(req)
    response = http_request("POST", "/events/restSearch", data=json.dumps(req))
    return response


@action(name="Get Event Detail")
def get_event(Event_ID):
    """
    Retrieves the most recent X number of events
    :param Event_ID: The Event_ID from previous step. If none available, you can do ='3223' where 3223 is the event_id.
    :return:
    """
    response = http_request("GET", "/events/view/"+Event_ID)
    return response 
    
@action(name="Add Event")
def add_event(org_id, uuid, info: JinjaTemplatedStr, event_creator_email):
    """
    Publish the named event with requred and optional fields
    :param org_id: 10 characters or less organizationId, eg, ="12334", you can find this from the organization page.
    :param uuid: 36 or less characters uniquely identifies this event. An event_id will be created for you afterward.
    :param info: the description of this event. This is a Jinja template form which allow you to format the string
    :param event_creator_email: the creator's email address, optional, eg: ="monty@logichub.com"
    :optional event_creator_email: True
    :return:
    """
    req = {"date": datetime.date.today().strftime('%Y-%m-%d'), "org_id": org_id, "orgc_id":org_id, "uuid":uuid, "info":info}
    if THREAT_LEVEL.read():
        req['threat_level_id'] = THREAT_LEVEL.read()
    else:
        req["threat_level_id"] = "4"
    if DISTRIBUTION.read():
        req['distribution'] = DISTRIBUTION.read()
    else:
        req['distribution'] = "0"
    if ANALYSIS.read():
        req['analysis'] = ANALYSIS.read()    
    else:
        req['analysis'] = "0"
    if event_creator_email:
        req["event_creator_email"] = event_creator_email
    print(req)
    response = http_request("POST", "/events/add", data=json.dumps(req))
    return response      

@action(name="Publish Event")
def publish_event(Event_ID):
    """
    Publish the named event
    :param Event_ID: The Event_ID from previous step. If none available, you can do ='3223' where 3223 is the event_id.
    :return:
    """
    response = http_request("POST", "/events/publish/"+Event_ID)
    return response  

@action(name="Unpublish Event")
def unpublish_event(Event_ID):
    """
    Unpublish the named event
    :param Event_ID: The Event_ID from previous step. If none available, you can do ='3223' where 3223 is the event_id.
    :return:
    """
    response = http_request("POST", "/events/unpublish/"+Event_ID)
    return response 
    
@action(name="Delete Event")
def delete_event(Event_ID):
    """
    Delete the named event
    :param Event_ID: The Event_ID from previous step. If none available, you can do ='3223' where 3223 is the event_id.
    :return:
    """
    response = http_request("DELETE", "/events/delete/"+Event_ID)
    return response     

@action(name="All Events")
def all_events():
    """
    Retrieves all events. Warning: this could be too much
    :return:
    """
    params = {}
    params["sort"] = "timestamp"
    params["direction"] = "desc"
    params["minimal"] = MINIMAL.read()
    response = http_request("POST", "/events/index", data=json.dumps(params))
    return response

def http_request(method, url_suffix, params={}, data=None, files=None):
    HEADERS = {
        'Authorization': API_TOKEN.read(),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    res = requests.request(method, URL.read() + url_suffix, verify=verify_ssl.verify_ssl_enabled(), params=params,
                           data=data, headers=HEADERS, files=files)
    if res.status_code not in {200, 201}:
        print(res.status_code)
        print(res.text)
    try:
        return res.json()
    except ValueError:
        return None
