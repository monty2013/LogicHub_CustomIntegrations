"""
name: Azure Storage Table - Opensource
description: This is a community provided integration for users to use as is and open source. This integration uses https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/tables/azure-data-tables
logoUrl: https://salespublic.s3.amazonaws.com/storage.png
"""

import time
import json
from lhub_integ.params import ConnectionParam, ActionParam, InputType, JinjaTemplatedStr, DataType, ValidationError
from lhub_integ.common import input_helpers, file_manager_client, validations, verify_ssl
from lhub_integ import action, connection_validator
from azure.data.tables import TableServiceClient, TableClient
from azure.core.credentials import AzureNamedKeyCredential
from azure.core.exceptions import HttpResponseError, ResourceExistsError
import datetime

ACCOUNT_NAME = ConnectionParam("ACCOUNT_NAME",
                               description="This is your account name",
                               input_type=InputType.TEXT)
ACCESS_KEY = ConnectionParam("ACCESS_KEY",
                             description="This is the access key",
                             input_type=InputType.PASSWORD)


@action(name="List Tables")
def list_table():
    """
    List all tables under this account name
    :return: a list of table_names
    """
    table_listing = []
    credential = AzureNamedKeyCredential(ACCOUNT_NAME.read(), ACCESS_KEY.read())
    with TableServiceClient(endpoint="https://" + ACCOUNT_NAME.read() + ".table.core.windows.net",
                            credential=credential) as table_service:
        list_tables = table_service.list_tables()
        for table in list_tables:
            table_listing.append({"table_name": table.name})
        return table_listing
    return None

@action(name="Create Table")
def create_table(table_name):
    """
    Creating a table under this account name
    :param table_name: the name of the table, if not defined by previous nodes, you can ="table_name". Table name has to be in a format supported by Azure.
    :return:
    """
    credential = AzureNamedKeyCredential(ACCOUNT_NAME.read(), ACCESS_KEY.read())
    with TableServiceClient(endpoint="https://" + ACCOUNT_NAME.read() + ".table.core.windows.net",
                            credential=credential) as table_service:
        table_client = table_service.create_table_if_not_exists(table_name=table_name)
    return {"message":"created"}

# todo: Will implement the delete table action later

@action(name="Insert Entity")
def insert_entity(table_name, entity):
    """
    Insert a row of data into this database
    :param table_name: the name of the table, if not defined by previous nodes, you can ="table_name". Table name has to be in a format supported by Azure.
    :param entity: a json string that defines the data entity to be inserted. Data must include PartitionKey and RowKey
    :return:
    """
    entity = json.loads(entity)
    credential = AzureNamedKeyCredential(ACCOUNT_NAME.read(), ACCESS_KEY.read())
    with TableServiceClient(endpoint="https://" + ACCOUNT_NAME.read() + ".table.core.windows.net",
                            credential=credential) as table_service:
        table_client = table_service.get_table_client(table_name=table_name)
        try:
            resp = table_client.create_entity(entity=entity)
            print(resp)
            return {"message":"inserted"}
        except ResourceExistsError:
            print("Entity already exists")
            return {"message":"failed"}
        except HttpResponseError as e:
            return {"message":e.message, "status":e.status_code, "reason":e.reason}
            
@action(name="Query Entities")
def query_entities(table_name, filters):
    """
    Query for Entities with the filters
    :param table_name: the name of the table, if not defined by previous nodes, you can ="table_name". Table name has to be in a format supported by Azure.
    :param filters: A string that specifies the filter, eg, "RowKey eq '114'". More reference at https://docs.microsoft.com/en-us/rest/api/storageservices/querying-tables-and-entities
    :optional filters: True
    :return:
    """
    returnVal = []
    credential = AzureNamedKeyCredential(ACCOUNT_NAME.read(), ACCESS_KEY.read())
    with TableServiceClient(endpoint="https://" + ACCOUNT_NAME.read() + ".table.core.windows.net",
                            credential=credential) as table_service:
        table_client = table_service.get_table_client(table_name=table_name)
        try:
            resp = table_client.query_entities(query_filter=filters)
            for entity_chosen in resp:
                returnVal.append(json.dumps(entity_chosen))
            if returnVal :
                return returnVal
            return {"message":"zero match"}
        except Exception as e:
            return {"message":str(e)} 
            
@action(name="List Entities")
def list_entities(table_name):
    """
    Query for the data with the filters
    :param table_name: the name of the table, if not defined by previous nodes, you can ="table_name". Table name has to be in a format supported by Azure.
    :return:
    """
    returnVal=[]
    credential = AzureNamedKeyCredential(ACCOUNT_NAME.read(), ACCESS_KEY.read())
    with TableServiceClient(endpoint="https://" + ACCOUNT_NAME.read() + ".table.core.windows.net",
                            credential=credential) as table_service:
        table_client = table_service.get_table_client(table_name=table_name)
        try:
            resp = table_client.list_entities()
            for entity_chosen in resp:
                returnVal.append(json.dumps(entity_chosen))
            return returnVal
        except Exception as e:
            return {"message":str(e)}    
            
@action(name="Delete Entity")
def delete_entity(table_name, PartitionKey, RowKey):
    """
     for the data with the filters
    :param table_name: the name of the table, if not defined by previous nodes, you can ="table_name". Table name has to be in a format supported by Azure.
    :param PartitionKey: the column holds the Partition Key, if not defined by previous nodes, you can ="PartitionKey_Value". 
    :param RowKey: the column holds the Row Key, if not defined by previous nodes, you can ="RowKey_value". 
    :return:
    """
    returnVal=[]
    credential = AzureNamedKeyCredential(ACCOUNT_NAME.read(), ACCESS_KEY.read())
    with TableServiceClient(endpoint="https://" + ACCOUNT_NAME.read() + ".table.core.windows.net",
                            credential=credential) as table_service:
        table_client = table_service.get_table_client(table_name=table_name)
        try:
            resp = table_client.delete_entity(partition_key=PartitionKey, row_key=RowKey)
            return {"message":"deleted"}
        except Exception as e:
            return {"message":str(e)}                
