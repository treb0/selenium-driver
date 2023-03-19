
# ## driver
# import importlib
# import os,sys
# currentDir = os.getcwd()
# print(currentDir)
# os.chdir('..') # .. to go back one dir | you can do "../aFolderYouWant"
# sys.path.insert(0, os.getcwd())
# from chromedriver import *
# os.chdir(currentDir) # to go back to your home directory



from chromedriver import *

from time import sleep

import sys
import pandas as pd

from bs4 import BeautifulSoup

import random

# Selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

from webdriver_manager.chrome import ChromeDriverManager


########################################################################################################################

# view display detected when headless

# open chromedriver
rel_path_to_selenium = ''
rel_path_to_chrome = ''
driver = open_chromedriver(rel_path_to_selenium, rel_path_to_chrome, extensions=['veepn']
                          ,headless=True
                          ,time_zone = 'America/Toronto'
                           )

########################################################################################################################

VPN_COUNTRY = 'Canada'
VPN_REGION = 'Ontario'
VEEPN_COUNTRY = VPN_COUNTRY
VEEPN_REGION = VPN_REGION

logged_in = driver.verify_ip(VPN_COUNTRY, VPN_REGION, VEEPN_COUNTRY, VEEPN_REGION)

########################################################################################################################

driver.get_browser_details()

########################################################################################################################
