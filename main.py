from bs4 import BeautifulSoup as btfs
import requests
import pandas as pd
from datetime import date
from datetime import datetime, timezone

def request_general_overview_data(session, url):

    ### General Overview
    # https://www.investing.com/commodities/crude-oil
    response = session.get(url)
    response.raise_for_status() 
    soup = btfs(response.text, 'html.parser')

    header_details = soup.find('div', attrs={'data-test': 'instrument-header-details'})

    price_last = header_details.find('div', attrs={'data-test': 'instrument-price-last'}).string
    print("price_last: ", price_last)
    price_change = ''
    for string in header_details.find('span', attrs={'data-test': 'instrument-price-change'}).strings:
        if string != '+':
            price_change = string
    print("price_change: ", price_change)
    price_change_percent = ''
    
    for string in header_details.find('div', attrs={'data-test': 'instrument-price-change-percentage'}).strings:
        if string != '(' or string != '%)':
            price_change_percent = string
            break

    print("price_change_percent: ", price_change_percent)

    time_label = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    print("time_label: ", time_label)

    extracted_data = {}

    dl_tag = soup.find('dl')

    if dl_tag:

        for div in dl_tag.find_all('div', recursive=False):
            dt_tag = div.find('dt')
            dd_tag = div.find('dd')

            if dd_tag and 'data-test' in dd_tag.attrs:
                data_test_attribute = dd_tag['data-test']
                extracted_data[data_test_attribute] = dd_tag.text.strip()
            elif dt_tag and 'data-test' in dt_tag.attrs:
                data_test_attribute = dt_tag['data-test']
                extracted_data[data_test_attribute] = dt_tag.text.strip()

    # Print the extracted data to verify
    for key, value in extracted_data.items():
        print(f"{key}: {value}")

def request_historical_data(session, url):
    try:
        response = session.get(url)
        response.raise_for_status() 
        soup = btfs(response.text, 'html.parser')

        table = soup.find('table', class_='freeze-column-w-1')

        cols = []
        for th in table.thead.tr.find_all('th'):
            if th.div.button.span.string != 'Date':
                cols.append(th.div.button.span.string)

        tbody = table.tbody

        rows = []
        indices = []
        for tr in tbody.find_all('tr'):
            row = []
            for td in tr.find_all('td'):
                if td.time:
                    indices.append(td.time['datetime'])
                    continue
                row.append(td.string)
            rows.append(row)
            
        stats_summary = {}

        stats_grid = soup.find('div', class_=['md:after:content-none'])

        for stat in stats_grid.find_all('div'):
            if stat.div:
                name = ''
                for string in stat.div.strings:
                    name = string
                    break
                value = stat.div.next_sibling.string

                stats_summary[name] = value
        
        df = pd.DataFrame(rows, columns=cols, index=indices)
        df.attrs = stats_summary
        return df
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def get_commodity_history(session):
    # commodities = ['crude-oil', 'natural-gas', 'copper', 'gold']
    commodities = ['crude-oil']
    base_url = 'https://www.investing.com/commodities/'
    # for commodity in commodities:
    #     history_url = base_url + commodity + '-historical-data'
    #     df = request_historical_data(session, history_url)
    #     filename = f'{commodity}-historical-{date.today()}.pkl'
    #     df.to_pickle(filename)

    overview_url = base_url + 'crude-oil'
    request_general_overview_data(session, overview_url)


session = requests.Session()
session.headers.update({'User-Agent': 'commodity-futures-bot/1.0'})

get_commodity_history(session)
