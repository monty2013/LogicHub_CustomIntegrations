"""
name: Twinwave
description: This is a community  provided integration for users to use as is and open source for all.
logoUrl: https://avatars.githubusercontent.com/u/48530599
"""
import requests
import time
import json
from lhub_integ.params import ConnectionParam, ActionParam, InputType, JinjaTemplatedStr, DataType, ValidationError
from lhub_integ.common import input_helpers, file_manager_client, validations, verify_ssl
from lhub_integ import action,connection_validator
import datetime

URL = ConnectionParam("URL",
                      description="This is the API endpoint with API version. For example, https://api.twinwave.io/v1",
                      input_type=InputType.TEXT,
                      default="https://api.twinwave.io/v1")
API_TOKEN = ConnectionParam("API_TOKEN",
                            description="You will need to get this Token from Twinwave UI",
                            input_type=InputType.PASSWORD)


# action type for add or delete rules
USERNAME = ActionParam("USERNAME",
                               description="filter by this username", optional=True,
                               input_type=InputType.TEXT, default=None,
                               action="recent_jobs")

SOURCE = ActionParam("SOURCE", description="filter by this Source, eg, ui or api", optional=True,
                                input_type=InputType.TEXT, default=None,
                                action="recent_jobs")

STATE = ActionParam("STATE", description="filter by this state, eg, pending, done, error, inprogress",
                               input_type=InputType.TEXT, optional=True,
                               default=None, action="recent_jobs")

JOB_COUNT = ActionParam("JOB_COUNT", description="Number of recent jobs to retrieve",
                                input_type=InputType.TEXT, data_type=DataType.INT, default="10", action="recent_jobs")

PRIORITY = ActionParam("PRIORITY", description="The job's priority relative to other jobs: 0-255, default is 10", optional=True,
                                input_type=InputType.TEXT, data_type=DataType.INT, default="10", action=["submit_url","submit_file"])
PROFILE = ActionParam("PROFILE", description="An optional profile name that defines the analysis behavior to be used during the analysis for this job. Default profile will be used if none specified.",
                                input_type=InputType.TEXT, optional=True, default=None, action=["submit_url","submit_file"])


START_TIME_MS = input_helpers._get_safe_stripped_env_integer('__execution_start_time_ms')
END_TIME_MS = input_helpers._get_safe_stripped_env_integer('__execution_end_time_ms')

@connection_validator
def validate_connections():
    if not URL.read():
        return [ValidationError(message="Parameter must be defined", param=URL)]

    if not API_TOKEN.read():
        return [ValidationError(message="Parameter must be defined", param=API_TOKEN)]

    url = f"{URL.read()}/engines"


    try:
        response = requests.get(url, headers={'Content-Type': 'application/json', 'X-API-KEY':API_TOKEN.read()})
        return response.raise_for_status()
    except Exception as ex:
        return [ValidationError(message=f"Authentication Failed")]


@action(name="Recent Jobs")
def recent_jobs():
    """
    Retrieves the most rent x number of jobs.
    :param query_string: This is the query string in Jinja template. For example 1, service=exchange&event=securityrisk&limit=10 or the querystring can be the next_link from previous get_logs.
    :return:
    """
    params = {}
    params["count"] = JOB_COUNT.read()
    if USERNAME.read():
        params["username"] = USERNAME.read()
    if SOURCE.read():
        params["source"] = SOURCE.read()
    if STATE.read():
        params["state"] = STATE.read()
    response = http_request("GET", "/jobs/recent",params=params)
    return response

@action(name="Wait for Job Completion")
def wait_for_job_completion(job_id):
    """
    This action will check for job status and sleep wait every 10 until the job completes or it will action_time_out.
    :param job_id: Job ID from previous steps
    :return:
    """
    while True:
        response = http_request("GET", "/jobs/" + job_id)
        if response.get("State") == 'done' :
            break
        time.sleep(10)
    return response

@action(name="Job Summary")
def job_summary(job_id):
    """
    Getting the Job Details
    :param job_id: Job ID from previous steps
    :return:
    """
    response = http_request("GET", "/jobs/" + job_id)
    return response

@action(name="Get Job Normalized Forensics")
def get_job_normalized_forensics(job_id):
    """
    Getting the Job Forensics
    :param job_id: Job ID from previous steps
    :return:
    """
    response = http_request("GET", "/jobs/" + job_id + "/forensics")
    return response

@action(name="Get Task Normalized Forensics")
def get_task_normalized_forensics(job_id, task_id):
    """
    Getting the Job Forensics
    :param job_id: Job ID from previous steps
    :param task_id: Task ID from previous steps
    :return:
    """
    response = http_request("GET", "/jobs/" + job_id + "/tasks/" + task_id + "/forensics")
    if response.get('errors'):
        return {"has_error": "true", "error_msg": (response.get('errors'))}
    return response


@action(name="Submit URL")
def submit_url(scan_url: JinjaTemplatedStr):
    """
    Submit an URL to be scanned
    :param scan_url: URL to be scanned - Jinja template enabled
    :return:
    """
    req = {"url": scan_url, "engines": []}
    if PRIORITY.read():
        req['priority'] = PRIORITY.read()
    if PROFILE.read():
        req['profile'] = PROFILE.read()

    response = http_request("POST", "/jobs/urls", data=json.dumps(req))
    return response

@action(name="Submit File")
def submit_file(file_id,file_name:JinjaTemplatedStr ):
    """
    Submit a file (pointed by file_id) to be scanned
    :param file_id: file_id from previous step 
    :param file_name: - Jinja template enabled
    :return:
    """
    header={'X-API-KEY': API_TOKEN.read()}
    data_file=file_manager_client.openFileForReading(file_id,"rb")
    print(data_file.size())
    payload = {"filename": file_name, "engines": []}
    if PRIORITY.read():
        payload['priority'] = PRIORITY.read()
    if PROFILE.read():
        payload['profile'] = PROFILE.read() 
    file_dict = {'filedata': data_file.fd.read()}
    res = requests.post(URL.read() + "/jobs/files", verify=verify_ssl.verify_ssl_enabled(), headers=header, data=payload, files=file_dict)
    if res.status_code not in {200, 201}:
        print(res.status_code)
        print(res.text)
    try:
        return res.json()
    except ValueError:
        return None

@action(name="Search Jobs and Resources")
def search(term: JinjaTemplatedStr, field: JinjaTemplatedStr, count: JinjaTemplatedStr,
           shared_only: JinjaTemplatedStr, submitted_by: JinjaTemplatedStr, timeframe:JinjaTemplatedStr,
           page: JinjaTemplatedStr, search_type:JinjaTemplatedStr):
    """
     Submit a search to query for jobs and resources
     :param term: Jinja-templated term to search for, ie: .exe or example.bat
     :optional term: True
     :param field: Jinja-templated field to search, "filename" "url" "tag" "sha256" "md5"
     :optional field: True
     :param count: Specify the maximum number of results to be returned. This has a hard limit of 100
     :optional count: True
     :param shared_only: Specify true to only search across Jobs (and their Resources) which have been shared
     :optional shared_only: True
     :param submitted_by: Jinja-templated Specify a username or part of a username (e.g. alice@example.com or alice)
     :optional submitted_by: True
     :param timeframe: Specify the maximum number of days back to search for results. Specify 0 for no limit.
     :optional timeframe: True
     :param page: The page for which you want results. This defaults to 1 the first page.
     :optional page: True
     :param search_type: Jinja-templated field Enum: "exact" "substring".
     :optional search_type: True
     :return:
     """
    query_params = {}
    if term:
        query_params['term'] = term
    if field:
        query_params['field'] = field
    if count:
        query_params['count'] = count
    if shared_only:
        query_params['shared_only'] = shared_only
    if submitted_by:
        query_params['submitted_by'] = submitted_by
    if timeframe:
        query_params['timeframe'] = timeframe
    if page:
        query_params['page'] = page
    if search_type:
        query_params['type'] = search_type
    response = http_request("GET", "/jobs/search", params=query_params)
    return response


def http_request(method, url_suffix, params={}, data=None, files=None):
    HEADERS = {
        'X-API-KEY': API_TOKEN.read(),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    res = requests.request(method, URL.read() + url_suffix, verify=verify_ssl.verify_ssl_enabled(), params=params, data=data,headers=HEADERS, files=files)
    if res.status_code not in {200, 201}:
        try:
            errors = ''
            for error in res.json().get('errors'):
                errors = '\n' + errors + error.get('detail')
            raise ValueError(
                f'Error in API call to Twinwave #1 [{res.status_code}] - [{res.reason}] \n'
                f'Error details: [{errors}]'
            )
        except Exception:
            raise ValueError(
                f'Error in API call to Twinwave #2 [{res.status_code}] - [{res.reason}]')
    try:
        return res.json()
    except ValueError:
        return None
