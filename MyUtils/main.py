"""
name: My Utilities
description: This is a set of utilities that will be handy at times.
logoUrl: https://s3.amazonaws.com/lhub-public/integrations/default-integration-logo.svg
"""

from markdownify import markdownify
from lhub_integ.params import ConnectionParam, ActionParam, InputType, JinjaTemplatedStr, DataType
from lhub_integ import action


base_path = "/opt/files/shared/integrationsFiles/"
events_base = "/opt/files/service/event_files/"

@action(name="HTML data to Markdown")
def markdown(input:JinjaTemplatedStr):
    """
    This action take an html formatted input and convert it to a markdown string.
    :param input: The data is expected to be in proper HTML format.
    :return:
    """
    html = markdownify(input)

    return {
        "has_error": "false", "html": html
    }
