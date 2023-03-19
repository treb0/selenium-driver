from time import sleep

import sys
import pandas as pd
import json

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

# os paths

from os import listdir
from os.path import isfile, join
import zipfile

import traceback


def open_chromedriver(rel_path_to_selenium
                     ,rel_path_to_chrome
                     ,profile = None
                     ,extensions = []
                     ,audio = False
                     ,headless = False
                     ,iproyal_json_path = None
                     ,time_zone = 'America/New_York'
                     ,change_user_agent = True
                     ,map_coordinates = {}
                     ):

    # list of available time zones: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

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
    if change_user_agent: options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")
    
    # Headless
    if headless: 
        #options.add_argument("--headless") # usando este no me funcionaban los extensions
        options.add_argument("--headless=new") # con este sí me funcionan las extensions (veepn)
        options.add_argument('--disable-gpu')

    # Profile
    if profile == 'incognito': options.add_argument("--incognito") ## chrome incognito mode
    elif type(profile) == int:
        options.add_argument(f'user-data-dir={rel_path_to_chrome}')
        options.add_argument(f'--profile-directory=Profile {profile}')

    # VPN
    if 'veepn' in extensions:
        # add vpn extension
        if rel_path_to_selenium != '': veepn_path = f'{rel_path_to_selenium}/extension_vpn.crx'
        else: veepn_path = 'extension_vpn.crx'
        options.add_extension(veepn_path)

    

    elif iproyal_json_path is not None:

        # get data from our json
        with open(iproyal_json_path, 'r') as f:
            vpn_json = json.load(f)
        PROXY_HOST = vpn_json['host'] # rotating proxy or host
        PROXY_PORT = vpn_json['port'] # port
        PROXY_USER = vpn_json['user'] # username
        PROXY_PASS = vpn_json['pass'] # password

        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };
        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

        pluginfile = 'proxy_auth_plugin.zip'
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        options.add_extension(pluginfile)

    # # Operating System >>> esto no funca porque hace que falle con "No matching capabilities found"
    # desired_caps = webdriver.DesiredCapabilities.CHROME.copy()
    # desired_caps['platform'] = "WINDOWS"
    # desired_caps['version'] = "10"
    
    #s = Service(ChromeDriverManager().install())

    #driver = Driver(service = s, options = options)

    #executable_path = rel_path_to_selenium + "chromedriver"
    executable_path = "chromedriver"
    driver = Driver(executable_path = executable_path
                   ,options = options
                   #,desired_capabilities=desired_caps
                   )

    # set timezone
    tz_params = {'timezoneId': time_zone}
    driver.execute_cdp_cmd('Emulation.setTimezoneOverride', tz_params)
        # al hacerlo varias veces sí cambia... podríamos codear una manera de asegurarnos de que cambie correctamente...
    driver.timezone = time_zone
    driver.tz_params = tz_params

    # set geo location >> not important since our chrome does not give its geo location...
    # map_coordinates = dict({
    #     "latitude": 43.8427, # toronto location
    #     "longitude": -79.4492,
    #     "accuracy": 100
    #     })
    # driver.execute_cdp_cmd("Emulation.setGeolocationOverride", map_coordinates)
    # driver.map_coordinates = map_coordinates

    # undetectable
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => false})"})

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

    # go to first tab
    driver.switch_to.window(driver.window_handles[0])

    # save driver properties
    driver.extensions = extensions
    driver.options = options
    driver.rel_path_to_selenium = rel_path_to_selenium
    driver.rel_path_to_chrome = rel_path_to_chrome
    driver.headless = headless


    return driver



class Driver(webdriver.Chrome):

    def send_action_keys(self, keys, pause_s=1):

        actions = ActionChains(self)

        if type(keys) != list: keys = [keys]
        
        for key in keys:
            if type(key) in [int, float]: key_final = str(key)
            else: key_final = key
            actions.send_keys(key_final).perform()
            sleep(pause_s)

    ################################################################################################################################################

        
    def open_new_tab(self,url=''):

        # open new tab
        self.execute_script("""window.open('')""")

        sleep(2)

        # focus on new tab
        self.switch_to.window(self.window_handles[len(self.window_handles)-1])

        sleep(0.5)

        # set parameters
        try: self.execute_cdp_cmd('Emulation.setTimezoneOverride', self.tz_params)
        except: pass
        try: driver.execute_cdp_cmd("Emulation.setGeolocationOverride", self.map_coordinates)
        except: pass
        # undetectable parameters
        self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => false})"})

        # open link
        self.open_link(url,mode = 'in')
        sleep(2)

        ################################################################################################################################################

    def close_current_tab(self):

        self.close()

        # go to first tab, so that driver is not stuck in closed tab
        self.switch_to.window(self.window_handles[0])

        return True

        ################################################################################################################################################

    def switch_to_tab(self,go_to_this_tab,refresh=False):
    
        go_to_this_tab = str(go_to_this_tab.lower())
        
        # Create df to store tabs data
        
        tabs = pd.DataFrame(columns = ['name','url','handle'])
        
        # Get window handles

        window_handles = self.window_handles
        
        # Read url and set name to each tab
        
        link_dict = {
            'fb':'https://www.facebook.com',
            'ip':'https://whatismyipaddress.com',
            'browser':'https://www.whatismybrowser.com/',
            'veepn':'chrome-extension://majdfhpaihoncoakbjgbdhglocklcgno/html/foreground.html',
            'veepn_premium':'https://veepn.com/pricing',
            'landing':'https://www.hellolanding.com',
            'clutch':'https://www.clutch.ca',
            'rent_seeker':'https://www.rentseeker.ca/'
            }
        
        # review if we already are in the tab and there is no need to review tabs
        try:
            current_tab_url = self.current_url
        except:
            # can fail if tab was manually closed
            self.switch_to.window(window_handles[0])
            current_tab_url = self.current_url

        # already in the correct web page?
        if link_dict[go_to_this_tab] in self.current_url: 
            
            if refresh:
                self.refresh()
                sleep(1)

            return True
        
        
        for i,handle in enumerate(window_handles):

            self.switch_to.window(handle)
            
            url = self.current_url

            name = 'undetected'  # default name of tab

            for link_name in link_dict:

                if link_dict[link_name] in url: 
                    name = link_name
                    break
        
            tabs.loc[len(tabs)] = [name,url,handle]
            
        # is there a tab with this url?
        if go_to_this_tab not in tabs['name'].tolist():

            # there is no tab with this url
            url = link_dict[go_to_this_tab]

            # create new tab with this url and focus on it
            self.open_new_tab(url)

            sleep(2)

            # review if opened fb logged in. exit if not logged in
            if go_to_this_tab == 'fb':
                sleep(3)
                create_new_account_buttons = self.find_elements(By.XPATH,'//a[@role="button"][@data-testid="open-registration-form-button"][text()="Create new account"]')
                if len(create_new_account_buttons) > 0: sys.exit('Not logged in to fb account. Exit program.')

            return f'new tab opened: {go_to_this_tab}'
        
        else:
            # there is a tab with this url
            go_index = tabs.index[tabs['name'] == go_to_this_tab].tolist()[0]

            # select tab
            self.switch_to.window(tabs['handle'][go_index])

            # refresh page?
            if refresh: self.refresh()

            return f'switched to tab: {go_to_this_tab}'
        

    ################################################################################################################################################

    def open_link(self
                 ,link_str
                 ,mode = 'equal'
                 ,retry = True
                 ,force_refresh = False
                 ):
    
        # mode = equal: function will iterate until it opens that exact same link
        # mode = in: opens that link and is ok with receving a link that contains extra text to the right
        
        if mode not in ('equal','in'): sys.exit('Bad mode entered for open_link')
        
        open_link_try = 0
        
        link_str = link_str.rstrip('/')
        
        sleep(2)

        driver_opened_new_page = False

        if force_refresh: self.get(link_str)
        sleep(5)
        
        while True:
            
            open_link_try += 1
            
            current_url_raw = self.current_url
            
            current_url_strict = current_url_raw.rstrip('/')
            
            if current_url_strict.find('?') > -1: current_url = current_url_strict[:current_url_strict.find('?')]
            else: current_url = current_url_strict
        
            if mode == 'equal':
                
                if link_str == current_url: return True

                elif (link_str in current_url) & driver_opened_new_page: 
                    # driver abrió una nueva pagina y la pagina te manda ya con utms o algo mas... qe se le va a hacer
                    # en definitiva se abrió correctamente la pagina
                    return True
        
            elif (mode == 'in') & (link_str in current_url): return True
        

            if not retry: return False
            
            else:
                # page is not correct

                if open_link_try >= 3:
                    
                    sys.exit(f'Error: open_link() has failed {open_link_try} times. System exit')

                else:

                    self.get(link_str)

                    driver_opened_new_page = True

                    sleep(5)
                  
    ################################################################################################################################################

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

    ################################################################################################################################################

    def veepn_close_rate_us_prompt(self):
        rate_us_prompts = self.find_elements(By.XPATH,'//div[@class="text"][text()="Click the stars to rate us"]')
        if len(rate_us_prompts) == 1:
            if rate_us_prompts[0].is_displayed():
                self.find_element(By.XPATH,'//button[@type="button"][@class="close"]').click()
                sleep(2)

    ################################################################################################################################################

    def set_veepn(self,country,region):

        if 'veepn' not in self.extensions: return 'VeePN not in driver extensions'

        self.switch_to_tab('veepn')

        sleep(10)

        # review if "upgrade to pro" screen
        get_access_buttons = self.find_elements(By.XPATH, '//button[@type="button"][@class="greenButton get-access-button"]')
        if len(get_access_buttons) == 1:
            get_access_buttons[0].click()
            sleep(3)
            self.switch_to_tab('veepn_premium')
            self.close_current_tab()
            self.switch_to_tab('veepn')
            sleep(4)

        # review if "new" screen
        next_buttons = self.find_elements(By.XPATH, '//button[@type="button"][@class="next"][text()="Continue"]')
        if len(next_buttons) == 1:
            next_buttons[0].click()
            sleep(2)
            self.find_element(By.XPATH, '//button[@type="button"][@class="next"][text()="Start"]').click()
            sleep(2)

        # review if "rate us" pop up
        self.veepn_close_rate_us_prompt()

        # Check if we are logged into veepn
        # open menu sidebar
        self.find_element(By.XPATH, '//button[@id="hamburger"]').click()
        sleep(2)
        soup = self.get_soup()
        log_ins = len(soup.find_all('button',text='Log In'))
        my_accounts = len(soup.find_all('div',text='My account'))
        if (log_ins == 1) & (my_accounts == 0):
            print('Not logged in. Proceeding to log in')
            self.find_element(By.XPATH, '//button[@type="button"][@class="loginButton greenButton"]').click()
            sleep(2)
            # load account data from json
            veepn_path = self.rel_path_to_selenium + 'veepn_access.json'
            with open(veepn_path, 'r') as f:
                veepn_access = json.load(f)
            self.send_action_keys(veepn_access['user'])
            sleep(2)
            self.send_action_keys(Keys.TAB)
            sleep(1)
            self.send_action_keys(veepn_access['password'])
            sleep(1)
            self.find_element(By.XPATH, '//button[@id="submit-form-button"]').click()
            print('Entered account & password: Logged in')
        elif (my_accounts == 1) & (log_ins == 0):
            print('Logged into veepn')
        else:
            print(f'Unexpected occurrances of log_ins ({log_ins}) and/or my_accounts ({my_accounts})')
        # close menu sidebar
        self.find_element(By.XPATH, '//div[@role="button"][@class="bg"]').click()
        sleep(2)

        # set the correct country and region
        while True:

            soup = self.get_soup()

            veepn_country = soup.find('div',{'class':'area-name'}).get_text().rstrip(' ').lstrip(' ')
            veepn_region = soup.find('div',{'class':'name'}).get_text().rstrip(' ').lstrip(' ')

            if (veepn_country == country) and (veepn_region == region): break

            else:
                self.find_element(By.XPATH, "//div[@class='region-wrapper']").click()

                sleep(2)

                ### click country
                try:
                    # first try to click country+region
                    self.find_element(By.XPATH, f"//div[@role='button']//span[@class='region-area'][contains(text(),'{country}')]/..//span[@class='region-city-name'][text()='{region}']").click()
                except:
                    # if not, we have to first click the country
                    self.find_element(By.XPATH, f"//div[@role='button']//div[@class='region-name-wrapper'][contains(text(),'{country}')]").click()
                    # and then the region
                    region_element = self.find_element(By.XPATH, f"//div[@role='button']//span[text()='{region}']")
                    self.scroll_to_element(region_element)
                    region_element.click()

                sleep(5)

        # review if "rate us" pop up
        self.veepn_close_rate_us_prompt()
        
        # turn on vpn
        while True:

            # check if connected
            soup = self.get_soup()
            status = soup.find('div',{'id':'mainBtn'})['class'][0]

            if status == 'connected': return True

            elif status == 'disconnected': 
                # click super button
                self.find_element(By.XPATH, f"//span[@class='button-clicker']").click()

            else:
                # se pone con status preConnected mientras esta connectado
                sleep(5)

    ################################################################################################################################################
    
    def verify_ip(self,country,region,veepn_country = '',veepn_region = ''):
        
        if country == '':
            print('Country not specified. System exit')
            sys.exit()
        
        elif region == '':
            print('Region not specified. System exit')
            sys.exit()

        elif country not in ['United States','Canada']:
            print('Un-recognized country. Add before runnig this funciton. System exit')
            sys.exit()
            

        while True:  

            # open web page or create new tab

            self.switch_to_tab('ip',refresh=True) 

            sleep(4)

            # scrape IP

            soup = self.get_soup()

            current_ip = soup.find("span", {"class": "address"}, {'id':'ipv4'}).get_text()

            current_country = soup.find('span',text='Country:').find_parent("p", {"class": "information"}).find_all('span')[1].get_text()
            current_region = soup.find('span',text='Region:').find_parent("p", {"class": "information"}).find_all('span')[1].get_text()
            current_city = soup.find('span',text='City:').find_parent("p", {"class": "information"}).find_all('span')[1].get_text()
            isp = soup.find('span',text='ISP:').find_parent("p", {"class": "information"}).find_all('span')[1].get_text()
            services = ''
            if len(soup.find_all('span',text='Services:')) == 1:
                services = soup.find('span',text='Services:').find_parent("p", {"class": "information"}).find_all('span')[1].get_text()


            print('')
            print(f'IP: {current_ip}')
            print(f'country: {current_country}')
            print(f'region: {current_region}')
            print(f'city: {current_city}')
            print(f'Internet Service Provider: {isp}')
            if services != '': print(f'Services: {services}')

            # IP validation
            if (current_country == country) & (region == current_region):
                
                print('')
                print(f'Success: {current_country}, {region} IP detected')
                    
                return True

            else:
                if 'veepn' in self.extensions: self.set_veepn(veepn_country,veepn_region)
                else: 
                    if self.headless: sys.exit('VPN not working')
                    else:
                        val = input(f"Set VPN to country: {country}, and region: {region}. Or enter 'exit' to exit")
                        if val == 'exit': sys.exit('user exit')

    ################################################################################################################################################

    def scroll(self,depth=9999999):

        self.execute_script(f"window.scrollTo(0,{depth});")

        sleep(3)

    ################################################################################################################################################


    def scroll_by(self,depth=200,sleep_s=3):

        self.execute_script(f"window.scrollBy(0,{depth});")

        sleep(sleep_s)

    ################################################################################################################################################

    def human_scroll_till_element_no_longer_visible(self,element,confirmations = 3):

        is_not_visible_confirmations = 0

        while True:

            #scroll_y = random.randint(1, 12)
            scroll_y = 10

            wait = random.randint(1, 5)/100

            self.execute_script(f"window.scrollBy(0,{scroll_y});")

            sleep(wait)

            is_visible = self.execute_script("var elem = arguments[0], "
                                    "box = elem.getBoundingClientRect(), "
                                    "cx = box.left + box.width / 2, "
                                    "cy = box.top + box.height / 2, "
                                    "e = document.elementFromPoint(cx, cy); "
                                    "for (; e; e = e.parentElement) { "
                                    "   if (e === elem) return true; "
                                    "} "
                                    "return false;", element)
            
            if not is_visible: 
                is_not_visible_confirmations += 1

            if is_not_visible_confirmations >= confirmations: break

        return True
    
    ################################################################################################################################################

    def human_scroll_by(self,depth):

        total_scroll = 0

        while depth > total_scroll:

            #scroll_y = random.randint(1, 12)
            scroll_y = 10

            wait = random.randint(1, 5)/100

            self.execute_script(f"window.scrollBy(0,{scroll_y});")

            sleep(wait)

            total_scroll = total_scroll + scroll_y

        return True
    
    ################################################################################################################################################

    def scroll_to_element(self, element):
        
        actions = ActionChains(self)
        
        actions.move_to_element(element).perform()

        sleep(2)

    ################################################################################################################################################
    
    # def human_scroll_to_element(self,depth): hay que programarlo, pero está dificil dado el infinite scroll donde no sabemos nuestra posicion... no sabemos si el element esta hacia arriba o abajo jaja

    #     total_scroll = 0

    #     while depth > total_scroll:

    #         #scroll_y = random.randint(1, 12)
    #         scroll_y = 10

    #         wait = random.randint(1, 5)/50

    #         self.execute_script(f"window.scrollBy(0,{scroll_y});")

    #         sleep(wait)

    #         total_scroll = total_scroll + scroll_y

    #     return True

    ################################################################################################################################################

    def send_keys_delete_clear_textbox(self,element,text_detection):

        element.click()

        sleep(3)

        while True:

            if text_detection == 'text': current_text_in_element = element.text

            else: current_text_in_element = element.get_attribute(text_detection)


            if current_text_in_element == '': return True

            else:

                # evitar que se quede dandole backspace, cuando el cursor está por delante de todo el texto, por lo que no borra nada
                self.send_action_keys(Keys.ARROW_RIGHT)

                self.send_action_keys(Keys.BACKSPACE)

                sleep(0.6)

        ################################################################################################################################################


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

    ################################################################################################################################################

    def multiple_elements_by_xpath(self
                                  ,xpath_list
                                  ,move_to = False
                                  ,click = False
                                  ,wait_s_after_move = 1
                                  ,wait_s_after_click=1
                                  ,exit_if_failure = True
                                  ):
        
        # detect and/or move to and/or click the first element possible

        for xpath in xpath_list:

            elements = self.find_elements(By.XPATH, xpath)

            if len(elements) > 0:

                element = elements[0]

                if move_to:
                    self.scroll_to_element(element)
                    sleep(wait_s_after_move)

                if click:
                    element.click()
                    sleep(wait_s_after_click)

                return xpath
            
        if exit_if_failure: sys.exit(f'no elements found. xpaths = {xpath_list}')
        else:
            return False
        
    ################################################################################################################################################

    def element_is_visible(self,element):
        is_visible = self.execute_script("var elem = arguments[0], "
                                    "box = elem.getBoundingClientRect(), "
                                    "cx = box.left + box.width / 2, "
                                    "cy = box.top + box.height / 2, "
                                    "e = document.elementFromPoint(cx, cy); "
                                    "for (; e; e = e.parentElement) { "
                                    "   if (e === elem) return true; "
                                    "} "
                                    "return false;", element)
        return is_visible

    ################################################################################################################################################

    def get_browser_details(self
                           ,max_tries = 5
                           ):

        print(f'''driver.capabilities.platformName: {self.capabilities['platformName']}''')

        get_tries = 0
        
        # try loop
        while True:

            try:

                self.switch_to_tab("browser",refresh=True)
                sleep(2)

                soup = self.get_soup()

                chrome_and_os = soup.find('div',{'aria-label':"We detect that your web browser is"}).find('a').get_text()

                computer_screen = soup.find('li',id="computer-screen").find('span').get_text()
                browser_window_size = soup.find('li',id="browser-window-size").find('span').get_text()
                hardware_type = soup.find('ul',id="technical-details").find('div',class_='key',text='Hardware Type').parent.find('div',class_="value").get_text()
                timezone = soup.find('ul',id="technical-details").find('div',class_='key',text='Browser GMT Offset').parent.find('div',class_="value").get_text()
                cpu_cores = soup.find('ul',id="technical-details").find('div',class_='key',text='No. of logical CPU cores').parent.find('div',class_="value").get_text()
                configured_laguages = soup.find('ul',id="technical-details").find('div',class_='key',text='Configured Languages').parent.find('div',class_="value").get_text()
                user_agent = soup.find('a',class_="user_agent",title="Your User Agent").get_text()

                print(f'chrome_and_os: {chrome_and_os}')
                # conflict between actual chrome and chromedriver user agent
                if len(soup.find_all('li',id="primary-browser-detection-backend-conflicts")) == 1:
                    print('conflict: ' + soup.find('li',id="primary-browser-detection-backend-conflicts").find('h1').get_text() + ' ' + soup.find('li',id="primary-browser-detection-backend-conflicts").find('div',class_="string-major").get_text().replace('\n','').replace('\r','').replace('\t','').rstrip(' ').lstrip(' '))
                elif len(soup.find_all('li',id="primary-browser-detection-backend-conflicts")) > 1:
                    sys.exit('Detected multiple conflicts')
                print(f'computer_screen: {computer_screen}')
                print(f'browser_window_size: {browser_window_size}')
                print(f'hardware_type: {hardware_type}') 
                print(f'timezone: {timezone}')
                print(f'CPU cores: {cpu_cores}')
                print(f'configured_laguages: {configured_laguages}')
                print(f'user_agent: {user_agent}')

                self.close_current_tab()

                break

            except:
            
                if get_tries >= max_tries:
                    print(f'Failed {max_tries} times to get browser details.')
                    print('traceback:')
                    traceback.print_exc()
                    sys.exit()

                else: get_tries += 1

    ################################################################################################################################################









