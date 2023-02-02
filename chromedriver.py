from time import sleep

import sys
import pandas as pd

from bs4 import BeautifulSoup

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

# os paths

from os import listdir
from os.path import isfile, join


def open_chromedriver(profile = None
                     ,extensions = []
                     ,audio = False
                     ):

    options = webdriver.ChromeOptions()
    
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) # > no me funciona en undetectable chromedriver
    options.add_experimental_option('useAutomationExtension', False) # > no me funciona en undetectable chromedriver
    options.add_argument('--disable-notifications')
    if not audio: options.add_argument("--mute-audio")
    options.add_argument("--disable-popup-blocking")

    # Options to avoid bot detection
    options.add_argument('--disable-blink-features=AutomationControlled') # el undetectable chromedriver recomienda sacarlo
    options.add_argument("--window-size=1282,814")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
    

    # Profile
    if profile == 'incognito': options.add_argument("--incognito") ## chrome incognito mode
    elif type(profile) == int:
        options.add_argument('user-data-dir=chrome')
        options.add_argument(f'--profile-directory=Profile {profile}')

    # Extensions
    if 'veepn' in extensions:
        # add vpn extension
        options.add_extension('chrome/extension_vpn.crx')

    
    #s = Service(ChromeDriverManager().install())

    #driver = Driver(service = s, options = options)

    executable_path="chromedriver"
    driver = Driver(executable_path = executable_path, options = options)
    
    sleep(10)

    if 'veepn' in extensions:

        print('veepn extension')

        # detect all open tabs, close VeePN tab

        while True:
            
            try:
                driver.switch_to.window(driver.window_handles[1])
                sleep(1)
                driver.close()
            except:
                break

    return driver



class Driver(webdriver.Chrome):
        


    def switch_to_tab(self,go_to_this_tab):
    
        go_to_this_tab = str(go_to_this_tab.lower())
        
        # Create df to store tabs data
        
        tabs = pd.DataFrame(columns = ['name','url','handle'])
        
        # Get window handles

        window_handles = self.window_handles
        
        # Read url and set name to each tab
        
        i = 0
        
        for i,handle in enumerate(window_handles):

            self.switch_to.window(handle)
            
            url = self.current_url
            
            if 'https://www.facebook.com' in url: name = 'fb'
            
            elif 'https://whatismyipaddress.com/' in url: name = 'ip'
            
            elif 'https://veepn.com/' in url: name = 'veepn'
            
            #elif 'https://speech-to-text-demo' in url: name = 'speech2text'
            
            else: name = 'undetected'
        
            tabs.loc[len(tabs)] = [name,url,handle]
            
        
        # get index of desired tab
            
        try:
            go_index = tabs.index[tabs['name'] == go_to_this_tab].tolist()[0]
        except:
            return 'error'
        

        # select tab
        
        self.switch_to.window(tabs['handle'][go_index])

        
        return f'tab opened: {go_to_this_tab}'
        

    def open_link(self
                 ,link_str
                 ,mode = 'equal'
                 ):
    
        # mode = equal: function will iterate until it opens that exact same link
        # mode = in: opens that link and is ok with receving a link that contains extra text to the right
        
        if mode not in ('equal','in'): sys.exit('Bad mode entered for open_link')
        
        open_link_try = 0
        
        link_str = link_str.rstrip('/')
        
        sleep(2)
        
        while True:
            
            try:
                
                open_link_try += 1
                
                current_url_raw = self.current_url
                
                current_url_strict = current_url_raw.rstrip('/')
                
                if current_url_strict.find('?') > -1: current_url = current_url_strict[:current_url_strict.find('?')]
                else: current_url = current_url_strict
            
                if (mode == 'equal') & (link_str == current_url): return None
            
                elif (mode == 'in') & (link_str in current_url): return None
            
                    
                elif open_link_try > 5:
                    
                    sys.exit(f'Error: open_link() has failed {open_link_try} times. System exit')

                else:

                    self.get(link_str)

                    sleep(5)
                    
            except:
                pass

    def get_soup(self,time_seconds=5):
    
        soup = ''
        
        soup_try = 0
        
        while soup_try < time_seconds:
            
            try:
                soup = BeautifulSoup(self.page_source,'html.parser')
                
                if soup != '': return soup
                
            except:
                soup_try += 1
                sleep(1)
                
            
    def verify_ip(self):
        
        print('')
        
        while True:
            
            try:

                my_ip_link = 'https://whatismyipaddress.com/'

                # la pagina neceista cargar e incluso me frena cloudflare, por lo que habrá que tener el tab abierto

                tab_action = self.switch_to_tab('ip')

                if tab_action == 'error':

                    self.execute_script(f"""window.open('{my_ip_link}')""")

                else:

                    self.refresh()

                sleep(2)

                # scrape IP

                soup = self.get_soup()

                current_ip = soup.find("span", {"class": "address"}, {'id':'ipv4'}).get_text()

                print(f'IP: {current_ip}')

                # IP validation
                if current_ip.split('.')[0] == '141':
                    
                    print('Success: New Jersey IP detected')
                    
                    switch_result = self.switch_to_tab('fb')
                    
                    if switch_result == 'error': self.switch_to.window(self.window_handles[0])
                        
                    return True
                
                elif current_ip.split('.')[0] == '51':
                    
                    print('Success: Oregon detected')
                    
                    switch_result = self.switch_to_tab('fb')
                    
                    if switch_result == 'error': self.switch_to.window(self.window_handles[0])
                        
                    return True
                
                elif current_ip.split('.')[0] in ('135','147'):
                    
                    print('Success: Virginia detected')
                    
                    switch_result = self.switch_to_tab('fb')
                    
                    if switch_result == 'error': self.switch_to.window(self.window_handles[0])
                        
                    return True
                
                else:
                    val = input("Put New Jersey IP")
                    
                    if val == 'error': sys.exit('induced error')
                    
            except:
                
                pass

    def scroll(self):

        self.execute_script("window.scrollTo(0,9999999);")

    def send_keys_delete_clear_textbox(element,text_detection):

        element.click()

        sleep(3)

        while True:

            if text_detection == 'text':

                current_text_in_element = element.text

            else:

                current_text_in_element = element.get_attribute(text_detection)

            if current_text_in_element == '': return True

            else:

                element.send_keys(Keys.BACKSPACE)

                sleep(0.6)

    def wait_for_page_load(self,url,checks,seconds_per_check):

        # url can be a string of 1 url, or a list of urls strings

        if type(url) == str: urls_check = [url]
        elif type(url) == list: urls_check = url
        else:
            sys.exit(f'unexpected type for url: {type(url)}')

        load_final_try = 0
            
        while True:

            if self.current_url in urls_check: return True

            else: 
                load_final_try += 1
                sleep(seconds_per_check)

            if load_final_try > checks: sys.exit(f'waiting for delivery web-page but not found. urls_check: {urls_check}')


    def verify_ip(self,VPN_COUNTRY = 'United States'):
    
        print('')
        
        while True:
            
            try:

                my_ip_link = 'https://whatismyipaddress.com/'

                # la pagina neceista cargar e incluso me frena cloudflare, por lo que habrá que tener el tab abierto

                tab_action = switch_to_tab('ip')

                if tab_action == 'error':

                    driver.execute_script(f"""window.open('{my_ip_link}')""")

                else:

                    driver.refresh()

                time.sleep(2)

                # scrape IP

                soup = get_soup()

                current_ip = soup.find("span", {"class": "address"}, {'id':'ipv4'}).get_text()

                country = soup.find('span',text='Country:').find_parent("p", {"class": "information"}).find_all('span')[1].get_text()
                region = soup.find('span',text='Region:').find_parent("p", {"class": "information"}).find_all('span')[1].get_text()
                city = soup.find('span',text='City:').find_parent("p", {"class": "information"}).find_all('span')[1].get_text()

                print(f'IP: {current_ip}')
                print(f'country: {country}')
                print(f'region: {region}')
                print(f'city: {city}')


                # IP validation
                if country == VPN_COUNTRY:
                    
                    print(f'Success: *{VPN_COUNTRY}* IP detected')
                    
                    switch_result = self.switch_to_tab(self,'fb')
                    
                    if switch_result == 'error': driver.switch_to.window(driver.window_handles[0])
                        
                    return True

                else:
                    val = input("Put New Jersey IP")
                    
                    if val == 'error': sys.exit('induced error')
                    
            except:
                
                pass










