from bs4 import BeautifulSoup
import requests
import pandas as pd
from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=ChromiumService(ChromeDriverManager().install()), options=options)

driver.get("https://python.org")
print(driver.title)
driver.close()