"""
name: ScreenShots
description: This Integration uses Selenium Webdriver to take screenshots. This is a custom integration provided 'as is' with open source and no warranty.
logoUrl: https://s3.amazonaws.com/lhub-public/integrations/default-integration-logo.svg
"""
from lhub_integ.params import ConnectionParam, ActionParam
from lhub_integ import action
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import uuid
import tempfile
import sys
import distutils.spawn

@action ("Screenshot File")
def screenshot_file(html_file_id):
    """
    When a file is downloaded into Logichub, there will be a File ID associated with that file. This action allow the user to take a screenshot by loading that file into a browswer session.
    :param html_file_id: File ID
    :label html_file_id: File ID
    :return:
    """
    
    download_directory = "/opt/files/shared/integrationsFiles"
    file_id = str(uuid.uuid4())+".png"
    
    html_file_location = os.path.join(download_directory, html_file_id)
    screenshot_target = os.path.join(download_directory, file_id)
    
    driver = make_driver()
    enable_download_in_headless_chrome(driver, download_directory)
    _ = get_screenshot_for_html_file(driver, html_file_location, screenshot_target)
    driver.quit()
    
    return {
        "lhub_file_id": file_id,
    }

@action ("Screenshot HTML data column")
def screenshot_html_field(html_column):
    """
    When a field contining a HTML document, this action allow the user to load that HTML document into a browser to capture the screenshot.
    :param html_column: html file content data column
    :label html_column: HTML Data Column
    :return:
    """
    
    download_directory = "/opt/files/shared/integrationsFiles"
    file_id = str(uuid.uuid4())+".png"
    
    tmp_directory = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
    os.mkdir(tmp_directory)
    
    html_file_location = os.path.join(tmp_directory, "tmp.html")
    with open(html_file_location, "w") as output_file:
      print(html_column, file=output_file)
    screenshot_target = os.path.join(download_directory, file_id)
    
    driver = make_driver()
    enable_download_in_headless_chrome(driver, download_directory)
    _ = get_screenshot_for_html_file(driver, html_file_location, screenshot_target)
    driver.quit()
    
    return {
        "lhub_file_id": file_id,
    }
    

@action ("Screenshot URL")
def screenshot_url(url):
    """
    This action requires an URL input from it's parent step and it will output a File ID that can be attached to cases or emails
    :param url: URL
    :lable url: URL
    :return:
    """
    
    download_directory = "/opt/files/shared/integrationsFiles"
    file_id = str(uuid.uuid4())+".png"
    
    screenshot_target = os.path.join(download_directory, file_id)
    
    driver = make_driver()
    enable_download_in_headless_chrome(driver, download_directory)
    _ = get_screenshot_for_url(driver, url, screenshot_target)
    driver.quit()
    
    return {
        "lhub_file_id": file_id,
    }
    
def make_driver():
    chromedriver = distutils.spawn.find_executable("chromedriver")
    if not chromedriver:
        if os.path.exists('/usr/bin/chromedriver'):
            chromedriver = '/usr/bin/chromedriver'
        elif os.path.exists('/usr/local/bin/chromedriver'):
            chromedriver = '/usr/local/bin/chromedriver'
        else:
            try:
                raise FileNotFoundError("Chrome driver not found")
            except:
                raise IOError("Chrome driver not found")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(executable_path=chromedriver, options=chrome_options)


def enable_download_in_headless_chrome(browser, download_dir):
    # add missing support for chrome "send_command"  to selenium webdriver
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    browser.execute("send_command", params)


def get_screenshot_for_html_file(driver, html_file_path, target_path):
    driver.get('file://' + html_file_path)
    return driver.save_screenshot(target_path)
    
def get_screenshot_for_url(driver, url, target_path):
    driver.get(url)
    return driver.save_screenshot(target_path)
