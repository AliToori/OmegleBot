#!/usr/bin/env python3
"""
    *******************************************************************************************
    OmegleBot: Omegle Chat Bot
    Developer: Ali Toori, Full-Stack Python Developer
    Founder: https://boteaz.com/
    *******************************************************************************************
"""
import os
import pickle
import re
import json
import random
import logging.config
import time
import zipfile
from time import sleep
import pandas as pd
import pyfiglet
import concurrent.futures
from pathlib import Path
from datetime import datetime
from multiprocessing import freeze_support
from selenium import webdriver
from seleniumwire import webdriver

from selenium.common import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from twocaptcha import TwoCaptcha


class OmegleBot:
    def __init__(self):
        self.PROJECT_ROOT = Path(os.path.abspath(os.path.dirname(__file__)))
        self.file_settings = str(self.PROJECT_ROOT / 'BotRes/Settings.json')
        self.directory_downloads = str(self.PROJECT_ROOT / 'BotRes/Downloads/')
        self.url_omegle = "https://www.omegle.com/"
        self.proxies = self.get_proxies()
        self.user_agents = self.get_user_agents()
        self.settings = self.get_settings()
        self.twocaptcha_api_key = self.settings["Settings"]["2CaptchaAPIKey"]
        self.twocaptcha_solver = TwoCaptcha(api_key=self.twocaptcha_api_key)
        self.LOGGER = self.get_logger()
        self.logged_in = False
        driver = None

    # Get self.LOGGER
    @staticmethod
    def get_logger():
        """
        Get logger file handler
        :return: LOGGER
        """
        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,
            'formatters': {
                'colored': {
                    '()': 'colorlog.ColoredFormatter',  # colored output
                    # --> %(log_color)s is very important, that's what colors the line
                    'format': '[%(asctime)s,%(lineno)s] %(log_color)s[%(message)s]',
                    'log_colors': {
                        'DEBUG': 'green',
                        'INFO': 'cyan',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'bold_red',
                    },
                },
                'simple': {
                    'format': '[%(asctime)s,%(lineno)s] [%(message)s]',
                },
            },
            "handlers": {
                "console": {
                    "class": "colorlog.StreamHandler",
                    "level": "INFO",
                    "formatter": "colored",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "simple",
                    'encoding': 'utf-8',
                    "filename": "OmegleBot.log",
                    "maxBytes": 5 * 1024 * 1024,
                    "backupCount": 1
                },
            },
            "root": {"level": "INFO",
                     "handlers": ["console", "file"]
                     }
        })
        return logging.getLogger()

    @staticmethod
    def enable_cmd_colors():
        # Enables Windows New ANSI Support for Colored Printing on CMD
        from sys import platform
        if platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    @staticmethod
    def banner():
        pyfiglet.print_figlet(text='____________ OmegleBot\n', colors='RED')
        print('OmegleBot: Omegle Chat Bot\n'
              'Developer: Ali Toori, Full-Stack Python Developer\n'
              'Founder: https://boteaz.com/\n'
              '************************************************************************')

    def get_settings(self):
        """
        Creates default or loads existing settings file.
        :return: settings
        """
        if os.path.isfile(self.file_settings):
            with open(self.file_settings, 'r') as f:
                settings = json.load(f)
            return settings
        settings = {"Settings": {
            "NumberOfInstancesToRun": 1
        }}
        with open(self.file_settings, 'w') as f:
            json.dump(settings, f, indent=4)
        with open(self.file_settings, 'r') as f:
            settings = json.load(f)
        return settings

    # Get random user agent
    def get_user_agents(self):
        file_uagents = str(self.PROJECT_ROOT / 'BotRes/user_agents.txt')
        with open(file_uagents) as f:
            content = f.readlines()
        return [x.strip() for x in content]

    # Loads interests from local file
    def get_interests(self, instance_no):
        file_interests = str(self.PROJECT_ROOT / f'BotRes/Interests_{instance_no}.txt')
        with open(file_interests) as f:
            content = f.readlines()
        return [x.strip() for x in content]

    # Loads a list scripts from local file
    def get_script(self, instance_no):
        file_scripts = self.PROJECT_ROOT / f'BotRes/Script_{instance_no}.txt'
        # scripts = pd.read_csv(file_scripts, index_col=None)
        # return [script["Script"] for script in scripts.iloc]
        with open(file_scripts) as f:
            content = f.readlines()
        return [x.strip() for x in content]

    # Loads proxies from local CSV file
    def get_proxies(self):
        file_proxies = str(self.PROJECT_ROOT / 'BotRes/Proxies.csv')
        proxy_list = pd.read_csv(file_proxies, index_col=None)
        return [proxy for proxy in proxy_list.iloc]

    # Loads web driver with configurations
    def get_driver(self, proxy=True, headless=False):
        driver_bin = str(self.PROJECT_ROOT / "BotRes/bin/chromedriver.exe")
        service = Service(executable_path=driver_bin)
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--dns-prefetch-disable")
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        prefs = {"directory_upgrade": True,
                 "credentials_enable_service": False,
                 "profile.password_manager_enabled": False,
                 "profile.default_content_settings.popups": False,
                 # "profile.managed_default_content_settings.images": 2,
                 f"download.default_directory": f"{self.directory_downloads}",
                 "profile.default_content_setting_values.geolocation": 2
                 }
        options.add_experimental_option("prefs", prefs)
        options.add_argument(F'--user-agent={random.choice(self.user_agents)}')
        # Set a proxy based on type i.e. Authenticated or simple
        if proxy:
            proxy = random.choice(self.proxies)
            # Check if Username and Password are not empty
            # Set Authenticated proxy
            if not pd.isna(proxy["Username"]) and not pd.isna(proxy["Password"]):
                username = proxy["Username"]
                password = proxy["Password"]
                ip = proxy["IP"]
                port = proxy["Port"]
                httpproxy = f'http://{username}:{password}@{ip}:{str(port)}'
                httpsproxy = f'https://{username}:{password}@{ip}:{str(port)}'
                self.LOGGER.info(f'Using Auth Proxy: {httpsproxy}')
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
                                """ % (ip, port, username, password)
                plugin_file = str(self.PROJECT_ROOT / f'BotRes/Plugins/proxy_auth_plugin_{username}.zip')
                plugin_manifest_file = str(self.PROJECT_ROOT / f'BotRes/Plugins/manifest_{username}.zip')
                plugin_background_file = str(self.PROJECT_ROOT / f'BotRes/Plugins/background_{username}.zip')
                # with zipfile.ZipFile(plugin_file, 'w') as zp:
                #     zp.writestr('manifest.json', manifest_json)
                #     zp.writestr('background.js', background_js)
                # options.add_extension(plugin_file)
                seleniumwire_options = {
                    'proxy': {
                        'http': httpproxy,
                        'https': httpsproxy,
                        'no_proxy': 'localhost,127.0.0.1'  # excludes
                    },
                    'disable_capture': True
                }
            # Set simple proxy
            else:
                proxy = f'{proxy["IP"]}:{proxy["Port"]}'
                options.add_argument(f"--proxy-server={proxy}")

        if headless:
            options.add_argument('--headless')
        # driver = webdriver.Chrome(service=service, options=options)
        driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)
        return driver

    @staticmethod
    def wait_until_visible(driver, css_selector=None, element_id=None, name=None, class_name=None, tag_name=None, duration=10000, frequency=0.01):
        if css_selector:
            WebDriverWait(driver, duration, frequency).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
        elif element_id:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.ID, element_id)))
        elif name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.NAME, name)))
        elif class_name:
            WebDriverWait(driver, duration, frequency).until(
                EC.visibility_of_element_located((By.CLASS_NAME, class_name)))
        elif tag_name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.TAG_NAME, tag_name)))

    # Captcha solver for reCaptcha V2
    def solve_captcha(self, driver):
        # Check if captcha is appeared
        try:
            self.wait_until_visible(driver=driver, css_selector='[class="g-recaptcha"]', duration=1)
        except:
            return
        self.LOGGER.info(f'Solving captcha')
        captcha_page_url = "https://www.omegle.com/"
        site_key_v2 = "6LekMVAUAAAAAPDp1Cn7YMzjZynSb9csmX5V4a9P"
        captcha_response = self.twocaptcha_solver.solve_captcha(site_key=site_key_v2, page_url=captcha_page_url)
        captcha_token = captcha_response["code"]
        self.LOGGER.info(f'Captcha token: {captcha_token}')
        self.LOGGER.info(f'Submitting captcha')
        # self.wait_until_visible(driver=driver, css_selector='[id="g-recaptcha-response"]')
        driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML="{captcha_token}";')
        driver.execute_script(f"___grecaptcha_cfg.clients['0']['V']['V']['callback']('{captcha_token}');")
        self.LOGGER.info(f'Captcha submitted successfully')
        try:
            self.wait_until_visible(driver=driver, css_selector='[class="alert alert-warn"]', duration=3)
            alert = driver.find_element(By.CSS_SELECTOR, '[class="alert alert-warn"]').text[:-2]
            sleep(1)
            if 'A system error has occurred' in alert:
                self.LOGGER.info(f'An Error occurred: {alert}')
        except:
            pass

    # Sets interests for Omegle chat
    def set_interests(self, driver, interests):
        # Set Interests
        try:
            self.LOGGER.info(f"Setting chat interests: {interests}")
            self.wait_until_visible(driver=driver, css_selector='[class="newtopicinput"]')
            sleep(3)
            interest_input = driver.find_element(By.CSS_SELECTOR, '[class="newtopicinput"]')
            driver.execute_script("arguments[0].scrollIntoView();", interest_input)
            for i in interests:
                interest_input.send_keys(i)
                interest_input.send_keys(Keys.RETURN)
                sleep(1)
        except:
            self.LOGGER.info(f"Error while setting interests")

    # Change interests when a chat is disconnected
    def change_interests(self, driver, interests):
        # Change interests
        try:
            self.LOGGER.info(f"Changing chat interests: {interests}")
            # Click Settings link when chat disconnected: Find strangers with common interests (Settings)
            self.wait_until_visible(driver=driver, css_selector='[class="logtopicsettings"] a')
            driver.find_element(By.CSS_SELECTOR, '[class="logtopicsettings"] a').click()

            # Delete the previous interests
            self.wait_until_visible(driver=driver, css_selector='[class="topictagdelete"]')
            [interest.click() for interest in driver.find_elements(By.CSS_SELECTOR, '[class="newtopicinput"]')]

            # Set new interests
            interest_input = driver.find_element(By.CSS_SELECTOR, '[class="newtopicinput"]')
            driver.execute_script("arguments[0].scrollIntoView();", interest_input)
            for i in interests:
                interest_input.send_keys(i)
                interest_input.send_keys(Keys.RETURN)

            # Start New chat after changing interests
            dis = driver.find_element(By.CSS_SELECTOR, 'button[class="disconnectbtn"]')
            # Click New
            dis.click()
            self.LOGGER.info('New chat started !')
        except:
            self.LOGGER.info(f"Error while changing interests")

    # Start text Chat by clicking Text button
    def start_chat(self, driver, interests):
        # Set interests
        self.set_interests(driver=driver, interests=interests)

        # Click Text button
        try:
            self.LOGGER.info(f"Starting chat")
            self.wait_until_visible(driver=driver, css_selector='[id="textbtn"]')
            driver.find_element(By.CSS_SELECTOR, '[id="textbtn"]').click()
        except:
            self.LOGGER.info(f"Error while starting chat")

        # Accept Terms Of Service
        try:
            # Click checkbox 1st
            self.LOGGER.info(f"Clicking checkbox 1st")
            self.wait_until_visible(driver=driver, css_selector='p input[type="checkbox"]')
            driver.find_element(By.CSS_SELECTOR, 'p input[type="checkbox"]').click()
            sleep(1)
            # Click checkbox 2nd
            self.LOGGER.info(f"Clicking checkbox 2nd")
            driver.find_elements(By.CSS_SELECTOR, 'p input[type="checkbox"]')[1].click()
            sleep(1)
        except:
            self.LOGGER.info(f"Error while clicking checkboxes")

        # Confirm and Continue
        try:
            self.LOGGER.info(f"Confirm and Continue")
            self.wait_until_visible(driver=driver, css_selector='[value="Confirm & continue"]')
            driver.find_element(By.CSS_SELECTOR, '[value="Confirm & continue"]').click()
            sleep(1)
        except:
            self.LOGGER.info(f"Error while clicking Confirm and Continue")

        # Check status log to confirm connected chat
        try:
            self.LOGGER.info(f"Checking connection status")
            self.wait_until_visible(driver=driver, css_selector='[class="statuslog"]')

            # Check if server is connected
            status_log = driver.find_element(By.CSS_SELECTOR, '[class="statuslog"]').text
            if "Error connecting to server" not in status_log:
                self.LOGGER.info('Connected ....!')
                return True
            else:
                self.LOGGER.info(f'Server Connection issue: {status_log}')
                return False
        except:
            self.LOGGER.info(f"Error while checking connection status")
            return False

    # Get stranger's chat messages
    def get_stranger_messages(self, driver):
        msgs = []
        # while True:
        try:
            self.wait_until_visible(driver=driver, css_selector='[class="chatmsg "]', duration=3)
            stranger_msgs = driver.find_elements(By.CSS_SELECTOR, '[class="strangermsg"]')
            [msgs.append(msg.text) for msg in stranger_msgs]
            return msgs
            # break
        except:
            sleep(1)

    # Send chat message to stranger
    def send_chat_message(self, driver, msg='Hello !'):
        try:
            self.LOGGER.info(f"Sending message: {msg}")
            self.wait_until_visible(driver=driver, css_selector='[class="chatmsg "]', duration=5)
            send = driver.find_element(By.CSS_SELECTOR, '[class="chatmsg "]')
            send.send_keys(msg)
            send.send_keys(Keys.RETURN)
            self.LOGGER.info(f"Message has been sent")
            return True
        except:
            self.LOGGER.info('Error while sending chat message')
            self.solve_captcha(driver=driver)
            return False

    # Start a new chat by clicking New button thrice
    def next_chat(self, driver):
        try:
            self.LOGGER.info(f"Going to the next chat")
            self.wait_until_visible(driver=driver, css_selector='button[class="disconnectbtn"]', duration=5)
            dis = driver.find_element(By.CSS_SELECTOR, 'button[class="disconnectbtn"]')
            dis.click()
            dis.click()
            dis.click()
        except:
            self.LOGGER.info('Error while going to the next chat')

    # Check chat status, if Stranger has disconnected,
    def check_chat_status(self, driver):
        try:
            self.LOGGER.info("Checking chat status")
            # Check if Stranger has disconnected, it will show New chat button at the end of the messages
            self.wait_until_visible(driver=driver, css_selector='[class="newchatbtnwrapper"]', duration=3)
            new = driver.find_element(By.CSS_SELECTOR, '[class="newchatbtnwrapper"]')
            dis = driver.find_element(By.CSS_SELECTOR, 'button[class="disconnectbtn"]')

            # Save screenshot with current TimeStamp
            file_name = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
            screenshot_path = f"{self.directory_downloads}/ChatShots/{file_name}"
            driver.save_screenshot(f'{screenshot_path}.png')

            # Click New
            dis.click()
            self.LOGGER.info('New chat started !')
            return True
        except:
            self.LOGGER.info('Error while checking chat status')
            return False

    # Chat on Omegle with a interests and scripts
    def chat_omegle(self, driver, interests, script):
        base_url = "https://www.omegle.com/"
        # Define random waits to wait between sending messages
        waits = [6, 7, 8, 9]

        # To change interests or not, on a chat disconnect
        change_interests = self.settings["Settings"]["ChangeInterests"]
        wait_for_ip = self.settings["Settings"]["WaitForIP"]

        # Exit this driver on timeout
        timeout = time.time() + wait_for_ip * 60

        # Go to Omegle base url
        driver.get(base_url)

        # Chat continuously
        self.LOGGER.info(f"Chatting with strangers")

        # Start chat
        chat_started = self.start_chat(driver=driver, interests=interests)

        # Check if chat has started
        if chat_started:
            self.LOGGER.info(f"Chat has been started")

            self.LOGGER.info(f"Script {script}")
            while True:

                # Wait until timeout
                if time.time() > timeout:
                    self.LOGGER.info(f"Timeout, exiting this session !")
                    break

                for script_msg in script:
                    # script = random.choice(scripts)
                    # Try to solve captcha if appears
                    msg_sent = self.send_chat_message(driver=driver, msg=script_msg)
                    sleep(random.choice(waits))
                    stranger_msgs = self.get_stranger_messages(driver=driver)
                    self.LOGGER.info(f"Stranger's message: {str(stranger_msgs)}")
                    sleep(random.choice(waits))

                    # Check if chat is still connected
                    # if self.check_chat_status(driver=driver):
                    if msg_sent:
                        continue

                    # If chat is disconnected, change interests based on the input change_interests
                    else:
                        if change_interests:
                            self.change_interests(driver=driver, interests=interests)
                        # Skip this script loop and go to next one
                        break
                # Start next chat
                self.next_chat(driver=driver)
        else:
            self.LOGGER.info(f"Couldn't start chat, exiting ...")

    # Launch a chat instance for a script
    def launch_chat_instance(self, instance_no):
        while True:
            self.LOGGER.info(f"Launching chat instance: {instance_no}")
            
            # Initialize driver
            driver = self.get_driver()
    
            # Get script and interests
            script = self.get_script(instance_no=instance_no)
            interests = self.get_interests(instance_no=instance_no)
    
            # Chat Omegle
            self.chat_omegle(driver=driver, interests=interests, script=script)

    # Main method to handle all the functions
    def main(self):
        freeze_support()
        self.enable_cmd_colors()
        self.banner()
        self.LOGGER.info(f'OmegleBot launched')
        num_of_instances = self.settings["Settings"]["NumberOfInstancesToRun"]
        instances = [i + 1 for i in range(num_of_instances)]
        # Launch an OmegleBot instance for each script in a separate thread in a scalable way
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(instances)) as executor:
            results = executor.map(self.launch_chat_instance, instances)
            try:
                for x, result in results:
                    self.LOGGER.info(f'Results: {result}')
            except Exception as e:
                self.LOGGER.info(e)


if __name__ == '__main__':
    OmegleBot().main()
