"""
My customized VT Integration description
"""
import requests
from lhub_integ.params import ConnectionParam, ActionParam, InputType
from lhub_integ import action

API_KEY = ConnectionParam("API_KEY", description="Key in your API key here", input_type=InputType.PASSWORD)

@action
def scan(url):
    """
    Given the url, submit to VT for Scan
    :param url: Input String
    :return:
    """
    endpt_url = 'https://www.virustotal.com/vtapi/v2/url/scan'
    params = {'apikey': API_KEY.read(), 'url':url}
    response = requests.post(endpt_url, data=params)
    #print(response.json())
    return {"scan_id":response.json()['scan_id']}


@action
def report(scan_id):
    """
    Given the url, retrieve report from VT by Scan ID
    :param scan_id: Scann_ID from scan
    :return:
    """
    url = 'https://www.virustotal.com/vtapi/v2/url/report'
    params = {'apikey': API_KEY.read(), 'resource':scan_id}
    response = requests.get(url, params=params)
    #print(response.json())
    result=response.json()
    return {"positives":result['positives'],"total":result['total']}
