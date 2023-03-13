
## driver
import importlib
import os,sys
currentDir = os.getcwd()
print(currentDir)
os.chdir('..') # .. to go back one dir | you can do "../aFolderYouWant"
sys.path.insert(0, os.getcwd())
from chromedriver import *
os.chdir(currentDir) # to go back to your home directory


from time import sleep


import sys
import pandas as pd

from bs4 import BeautifulSoup

import random

import importlib
import os,sys
currentDir = os.getcwd()


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

print('begin')

driver = open_chromedriver(rel_path_to_selenium = '..'
                     ,rel_path_to_chrome = ''
                     ,profile = None
                     ,extensions = ['veepn']
                     ,audio = False
                     ,headless = True
                     )


################################################################################################

VPN_COUNTRY = 'Canada'
VPN_REGION = 'Ontario'
VEEPN_COUNTRY = VPN_COUNTRY
VEEPN_REGION = VPN_REGION

logged_in = driver.verify_ip(VPN_COUNTRY, VPN_REGION, VEEPN_COUNTRY, VEEPN_REGION)

print('test program finished!')

from datetime import datetime
print('')
print('datetime now:')
print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))