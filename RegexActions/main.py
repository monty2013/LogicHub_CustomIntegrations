"""
Regular expression based text processing. For example, find multi-matches or search for keywords.
"""
from lhub_integ.params import ConnectionParam, ActionParam
from lhub_integ import action
import re
import sys

REGEX_EXP = ActionParam("REGEX_EXP",description="enter a valid regular expression to multi-search", optional=False, action="extract_multi")
REGEX_EXP2 = ActionParam("REGEX_EXP2",description="enter a valid regular expression with named pattern", optional=False, action="extract_named")
KEYWORDS = ActionParam("KEYWORDS",description="enter a list of regular expressions with space separation.", optional=False, action="find_keywords")

@action(name="Extract Multi")
def extract_multi(search_from) :
    """
    extract the matching regular expression pattern multiple times.
    :param search_from: Column containing data to search from
    :return: all matched patterns.
    """
    regex = r'{}'.format(REGEX_EXP.read())
    return {"matched":re.findall(regex, search_from)}

@action(name="Extract Named")
def extract_named(search_from) :
    """
    extract the matching regular expression pattern in (?P<name>regex_pattern).
    :param search_from: Column containing data to search from
    :return: all matched patterns.
    """
    regex = r'{}'.format(REGEX_EXP2.read())
    pattern = re.compile(regex)
    m = pattern.match(search_from)
    if m: 
        return m.groupdict()    
    return {"matched":"none"}
    
@action(name="Find Keywords")
def find_keywords(search_from) :
    """
    This action will provide the results on how many matches
    :param search_from: Column containing data to search from
    :return: all matched patterns.
    """
    keywords = KEYWORDS.read().split(' ')
    matched = 0
    return_list = []
    for keyword in keywords :
        regex = r'{}'.format(keyword)
        val = len(re.findall(regex,search_from))
        if val > 0 :
            matched = matched + 1
        return_list.append({"keyword":keyword,"occurance":val})
    #report back
    matched_pct = int(100*matched/len(keywords))
    return {"result":{"matched_percentage": matched_pct, "details":return_list}}
