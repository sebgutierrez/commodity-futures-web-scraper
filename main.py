from bs4 import BeautifulSoup
import requests
import pandas as pd
import random

# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service

# from selenium.webdriver.chrome.service import Service as ChromiumService
# from webdriver_manager.chrome import ChromeDriverManager

# options = Options()
# options.add_argument('--headless')
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 (compatible; commodity-futures-bot/1.0)')
# driver = webdriver.Chrome(service=ChromiumService(ChromeDriverManager().install()), options=options)

session = requests.Session()
session.headers.update({'User-Agent': 'commodity-futures-bot/1.0'})

url = 'https://www.investing.com/commodities/crude-oil-historical-data'

try:
    response = session.get(url)
    response.raise_for_status() 
    soup = BeautifulSoup(response.content, 'html.parser')
    ### General Overview
    # https://www.investing.com/commodities/crude-oil
    h2 = soup.find('h2')

    # div data-test="instrument-header-details"
    ### div data-test="instrument-price-last"
    ### div data-test="instrument-price-change"
    ### data-test="instrument-price-change-percent"

    ## dl button dl

    # div data-test="key-info"

    ## dl 
    ### div (dt div div span Prev. Close) // div (dd span span[1])   ; data-test=prevClose
    ### div (dt div div span Open) // div (dd span span[1])   ; data-test=open
    ### div (dt span Day's Range) // div (dd (span[0] span[1]) + span[1] (-) + (span[2] span[1]))   ; data-test=dailyRange
    ### div (dt span 52 wk Range) // div (dd (span[0] span[1]) + span[1] (-) + (span[2] span[1]))   ; data-test=weekRange
    ### div (dt div div span Volume) // div (dd span span[1])    ; data-test=volume
    ### div (dt div div span 1-Year Change) // div (dd span span[1] -17.6 span[2] %)   ; data-test=oneYearReturn
    ### div (dt span Month) // div (dd Aug 25)   ;         data-test=month_date

    ## dl 
    ### div (dt span Settlement Day) // div (dd 07/21/2025)     ;    data-test=settlement_date
    ### div (dt span Base Symbol) // div (dd T) ;        data-test=base_symbol
    ### div (dt span Point Value) // div (dd 1 = $1000)   ; data-test=point_value

    ### General Historical Data
    # https://www.investing.com/commodities/crude-oil-historical-data


except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")