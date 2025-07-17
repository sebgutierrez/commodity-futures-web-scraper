import pickle
import requests
import pandas as pd
from bs4 import BeautifulSoup as btfs
from datetime import date, datetime, timezone
from pathlib import Path

def save_df(df, filename, commodity):
    commodity_path = Path.cwd() / commodity
    commodity_path.mkdir(exist_ok=True)
    df_path = commodity_path / filename
    if df_path.exists():
        loaded_df = pd.read_pickle(df_path)
        concatenated_df = pd.concat([df, loaded_df])
        if concatenated_df.shape[0] > 30:
            concatenated_df = concatenated_df[:30] 
        concatenated_df.to_pickle(df_path)
    else:
        df.to_pickle(df_path)

def scrape_historical_data(session, url, dataset_exists=False):
    try:
        response = session.get(url)
        response.raise_for_status() 
        soup = btfs(response.text, 'html.parser')

        table = soup.find('table', class_='freeze-column-w-1')

        column_names = []
        for th in table.thead.tr.find_all('th'):
            if th.div.button.span.string != 'Date':
                column_names.append(str(th.div.button.span.string))

        tbody = table.tbody

        historical_records = []
        timestamps = []
        for tr in tbody.find_all('tr'):
            historical_record = []
            for td in tr.find_all('td'):
                if td.time:
                    timestamps.append(str(td.time['datetime']))
                    continue
                elif td.string[-1] != 'K' and td.string[-1] != '%':
                    historical_record.append(float(td.string))
                    continue
                else:
                    historical_record.append(str(td.string))
            # If historical data has been previously stored, only look for the most recent data and stop the search early
            historical_records.append(historical_record)
            if len(historical_records) == 1 and dataset_exists == True:
                df = pd.DataFrame(historical_records, columns=column_names, index=timestamps)
                return df

        df = pd.DataFrame(historical_records, columns=column_names, index=timestamps)
        return df
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def get_commodity_history(session, base_url, commodities):
    for commodity in commodities:
        history_url = base_url + commodity + '-historical-data'
        history_filename = f'{commodity}-historical.pkl'
        df_path = Path.cwd() / commodity / history_filename
        if df_path.exists():
            df = scrape_historical_data(session, history_url, dataset_exists=True)
        else:
            df = scrape_historical_data(session, history_url)
            save_df(df, history_filename, commodity)

def scrape_overview_data(session, url):
    try:
        current_time = datetime.now(timezone.utc)
        time_day = current_time.day
        time_hour = current_time.hour
        time_minute = current_time.minute

        response = session.get(url)
        response.raise_for_status() 
        soup = btfs(response.text, 'html.parser')

        header_details = soup.find('div', attrs={'data-test': 'instrument-header-details'})

        header_data = []
        price_last = header_details.find('div', attrs={'data-test': 'instrument-price-last'}).string
        header_data.append(float(price_last))
        price_change = header_details.find('span', attrs={'data-test': 'instrument-price-change'}).text
        header_data.append(float(price_change))
        price_change_percent = ''
        for string in header_details.find('span', attrs={'data-test': 'instrument-price-change-percent'}).strings:
            if string == '(' or string == '%)':
                continue
            price_change_percent += string
        price_change_percent += '%'
        header_data.append(str(price_change_percent))

        dl_info = [time_day, time_hour, time_minute] + header_data
        dl_tag = soup.find('dl')

        if dl_tag:
            for div in dl_tag.find_all('div', recursive=False):
                dd_tag = div.find('dd')
                if dd_tag and 'data-test' in dd_tag.attrs:
                    dl_info.append(str(dd_tag.text.strip()))

        columns = ['Day', 'Hour', 'Minute', 'Last Price', 'Price Change', 'Price Change Percent', 'Prev. Close', 'Open', 'Day Range', '52 Week Range', 'Volume', '1-Year Change', 'Month', 'Contract Size']
        df = pd.DataFrame(data=[dl_info], columns=columns)
        return df
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def get_commodity_overview(session, base_url, commodities):
    for commodity in commodities:
        overview_url = base_url + commodity
        overview_filename = f'{commodity}-overview.pkl'
        df = scrape_overview_data(session, overview_url)
        save_df(df, overview_filename, commodity)

if __name__ == "__main__":
    session = requests.Session()
    session.headers.update({'User-Agent': 'commodity-futures-bot/1.0'})

    commodities = ['natural-gas', 'copper', 'crude-oil', 'gold']
    base_url = 'https://www.investing.com/commodities/'
    
    get_commodity_history(session, base_url, commodities)
    get_commodity_overview(session, base_url, commodities)