"""
name: TrendMicro Cloud Application Security
description: This integration uses TrendMicro's Cloud Application Security REST API. The details about the REST API can be found here: https://docs.trendmicro.com/en-us/enterprise/cloud-app-security-integration-api-online-help/getting-started-with.aspx
logoUrl: https://images.g2crowd.com/uploads/product/image/large_detail/large_detail_ac04b2920e7c3da93c9525a8fdba8f45/tippingpoint-security-management-system.png
"""
import requests
import json
from lhub_integ.params import ConnectionParam, ActionParam, InputType, JinjaTemplatedStr
from lhub_integ.common import input_helpers, verify_ssl
from lhub_integ import action
import datetime

URL = ConnectionParam("URL",
                      description="API Endpoint, pick your endpoint. Referencing the online doc here if needed https://docs.trendmicro.com/en-us/enterprise/cloud-app-security-integration-api-online-help/getting-started-with/understanding-the-ur.aspx",
                      input_type=InputType.SELECT, options= ["https://api.tmcas.trendmicro.com",
                                                             "https://api-eu.tmcas.trendmicro.com",
                                                             "https://api.tmcas.trendmicro.co.jp",
                                                             "https://api-au.tmcas.trendmicro.com",
                                                             "https://api.tmcas.trendmicro.co.uk",
                                                             "https://api-ca.tmcas.trendmicro.com",
                                                             "https://api.tmcas.trendmicro.com.sg",
                                                             "api-in.tmcas.trendmicro.com"], default="https://api.tmcas.trendmicro.com")
API_TOKEN = ConnectionParam("API_TOKEN",
                            description="API Token for 3rd party application. Read more at https://docs.trendmicro.com/en-us/enterprise/cloud-app-security-integration-api-online-help/getting-started-with/generating-an-authen.aspx",
                            input_type=InputType.PASSWORD)

SERVICE = ConnectionParam("SERVICE",
                      description="Either Exchange or GMail",
                      input_type=InputType.SELECT, options= ["exchange",
                                                             "gmail"], default="exchange")
SERVICE_PROVIDER = ConnectionParam("SERVICE_PROVIDER",
                      description="Either Office365 or Google",
                      input_type=InputType.SELECT, options= ["office365",
                                                             "google"], default="office365")

# action type for add or delete rules
RULE_ACTION_TYPE = ActionParam("EMAIL_ACTION_TYPE", description="Add one or multiple email senders, URLs, SHA-1 hash values, and SHA-256 hash values to or remove them from the blocked lists.",
                               input_type=InputType.SELECT, options=["create",
                                                                     "delete"], default="create", action="update_block_list")

EMAIL_ACTION_TYPE = ActionParam("EMAIL_ACTION_TYPE", description="Action to take on an email message.",
                               input_type=InputType.SELECT, options=["MAIL_DELETE",
                                                                     "MAIL_QUARANTINE"], default="MAIL_DELETE", action="email_action")
                                                                     
USER_ACTION_TYPE = ActionParam("USER_ACTION_TYPE", description="Action to take on an user account.",
                               input_type=InputType.SELECT, options=["ACCOUNT_DISABLE",
                                                                     "ACCOUNT_ENABLE_MFA",
                                                                     "ACCOUNT_RESET_PASSWORD",
                                                                     "ACCOUNT_REVOKE_SIGNIN_SESSIONS"], default="ACCOUNT_RESET_PASSWORD", action="user_action")
                                                                     
QUERY_ACTION_TYPE = ActionParam("QUERY_ACTION_TYPE", description="The type of action to take on.",
                               input_type=InputType.SELECT, options=["accounts",
                                                                     "mails"], default="mails", action="query_action")



START_TIME_MS = input_helpers._get_safe_stripped_env_integer('__execution_start_time_ms')
END_TIME_MS = input_helpers._get_safe_stripped_env_integer('__execution_end_time_ms')

@action(name="Get Security Logs")
def get_logs(query_string: JinjaTemplatedStr):
    """
    Retrieves security event logs of the services that Cloud App Security protects. Details at https://docs.trendmicro.com/en-us/enterprise/cloud-app-security-integration-api-online-help/supported-cloud-app-/log-retrieval-api/get-security-logs.aspx
    :param query_string: This is the query string in Jinja template. For example 1, service=exchange&event=securityrisk&limit=10 or the querystring can be the next_link from previous get_logs.
    :return:
    """
    response = http_request("GET", "/v1/siem/security_events?"+query_string)
    if response.get('errors'):
        return {"has_error": "true", "error_msg": (response.get('errors'))}
    return response
    

@action(name="Sweep for Email Messages")
def sweep_emails(query_string: JinjaTemplatedStr):
    """
    Searches email messages in Cloud App Security protected mailboxes for those that match meta information search criteria.
    :param query_string: This is the query string in Jinja template. For example 1, mailbox=user1@example1.com&
     start=2019-02-12T01:51:31.001Z&end=2019-03-12T01:51:31.001Z OR example 2, subject="wire transfer"&lastndays=2&limit=10 The details on how to create query is online at: https://docs.trendmicro.com/en-us/enterprise/cloud-app-security-integration-api-online-help/supported-cloud-app-/threat-investigation/sweep-for-email-mess.aspx .
    :return:
    """
    response = http_request("GET", "/v1/sweeping/mails?"+query_string)
    if response.get('errors'):
        return {"has_error": "true", "error_msg": (response.get('errors'))}
    return response

# Remediation Actions
@action(name="Get Blocked Lists")
def get_block_list():
    """
    Retrieves all blocked senders, URLs, SHA-1 hash values, and SHA-256 hash values that the administrator has configured through this API on Cloud App Security to quarantine Exchange Online email messages.
    :return:
    """
    response = http_request("GET", "/v1/remediation/mails")
    if response.get('errors'):
        return {"has_error": "true", "error_msg": (response.get('errors'))}
    return response

@action(name="Update Blocked Lists")
def update_block_list(rule_string: JinjaTemplatedStr):
    """
    Adds or removes senders, URLs, SHA-1 hash values, and/or SHA-256 hash values to or from the blocked lists on Cloud App Security.
    :param rule_string: This is the rule in Jinja template. For example,  "urls": ["https://test.example.com"], other rules can be senders, urls, filehashes, file256hashes
    :return:
    """
    post_data = {
        "action_type" : RULE_ACTION_TYPE.read(),
        "rule" : {
            rule_string
        }
    }
    response = http_request("POST", "/v1/remediation/mails", data=post_data)
    if response.get('errors'):
        return {"has_error": "true", "error_msg": (response.get('errors'))}
    return response

@action(name="Take Actions on Email Messages")
def email_action(mailbox: JinjaTemplatedStr, mail_message_id: JinjaTemplatedStr, mail_unique_id: JinjaTemplatedStr, mail_messge_delivery_time: JinjaTemplatedStr):
    """
    Takes actions on a batch of specified email messages, including deleting an email message and quarantining an email message.
    :param mailbox: Email address of an email message to take action on.
    :param mail_message_id: Internet message ID of an email message to take action on. It can be obtained from Cloud App Security Sweep for email messages API or Microsoft Graph API. This should be referenced from the sweep email action.
    :param mail_unique_id: 	Unique ID of an email message to take action on It can be obtained from Cloud App Security Sweep for email messages API or Microsoft Graph API. This should be referenced from the sweep email action.
    :param mail_messge_delivery_time: Date and time when an email message to take action on is sent. It can be obtained from Cloud App Security Sweep for email messages API or Microsoft Graph API or EWS API.
    :return:
    """
    post_data = [{
        "action_type": EMAIL_ACTION_TYPE.read(),
        "service": SERVICE.read(),
        "account_provider": SERVICE_PROVIDER.read(),
        "mailbox": mailbox,
        "mail_message_id": mail_message_id,
        "mail_unique_id": mail_unique_id,
        "mail_message_delivery_time": mail_messge_delivery_time
    }]
    response = http_request("POST", "/v1/mitigation/mails", data=post_data)
    if response.get('errors'):
        return {"has_error": "true", "error_msg": (response.get('errors'))}
    return response

@action(name="Take Actions on User Accounts")
def user_action(mailbox: JinjaTemplatedStr):
    """
    Takes actions on a batch of specified user accounts, including disabling a user account, requesting to enable multi-factor authentication (MFA) for a user account, requesting to reset password for a user account, and terminating all sign-in sessions of Microsoft services for a user account.
    :param mailbox: Email address of an email message to take action on.
    :return:
    """
    post_data = [{
        "action_type": USER_ACTION_TYPE.read(),
        "service": SERVICE.read(),
        "account_provider": SERVICE_PROVIDER.read(),
        "account_user_email": mailbox
    }]
    response = http_request("POST", "/v1/mitigation/accounts", data=post_data)
    if response.get('errors'):
        return {"has_error": "true", "error_msg": (response.get('errors'))}
    return response

@action(name="Query Action Results")
def query_action(batch_id: JinjaTemplatedStr):
    """
    Queries the results of actions on specified email messages or user accounts through Take Actions on User Accounts and Take Actions on Email Messages APIs.
    :param batch_id: From the previous action
    :return:
    """
    response = http_request("GET", "/v1/mitigation/"+QUERY_ACTION_TYPE.read()+"?batch_id="+batch_id)
    if response.get('errors'):
        return {"has_error": "true", "error_msg": (response.get('errors'))}
    return response    
    
    
@action(name="Test Connectivity")
def test():
    """
    This action will try to retrive one SIEM event
    :return:
    """
    response = http_request("GET", "/v1/siem/security_events?service=exchange&event=securityrisk&limit=5")
    if response.get('errors'):
        return {"has_error": "true", "error_msg": (response.get('errors'))}
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
    if res.status_code not in {200, 201}:
        try:
            errors = ''
            for error in res.json().get('errors'):
                errors = '\n' + errors + error.get('detail')
            raise ValueError(
                f'Error in API call to Sentinel One [{res.status_code}] - [{res.reason}] \n'
                f'Error details: [{errors}]'
            )
        except Exception:
            raise ValueError(f'Error in API call to TrendMicros Cloud Application Security [{res.status_code}] - [{res.reason}]')
    try:
        return res.json()
    except ValueError:
        return None
