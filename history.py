from bs4 import BeautifulSoup as btfs
import pandas as pd
from pathlib import Path
import pickle
import pytz
import requests

def strip_commas(string):
	stripped = ''
	for char in string:
		if char != ',':
			stripped += char
	return stripped

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
			column_names.append(str(th.div.button.span.string))

		tbody = table.tbody

		historical_records = []
		for tr in tbody.find_all('tr'):
			historical_record = []
			for td in tr.find_all('td'):
				if td.time:
					historical_record.append(str(td.time['datetime']))
					continue
				elif td.string[-1] != 'K' and td.string[-1] != '%':
					if td.string.find(',') != -1:
						td.string = strip_commas(td.string)
					historical_record.append(float(td.string))
					continue
				else:
					historical_record.append(str(td.string))
			# If historical data has been previously stored, only look for the most recent data and stop the search early
			historical_records.append(historical_record)
			if len(historical_records) == 1 and dataset_exists == True:
				df = pd.DataFrame(historical_records, columns=column_names)
				return df
		df = pd.DataFrame(historical_records, columns=column_names)
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

if __name__ == "__main__":
    session = requests.Session()
    session.headers.update({'User-Agent': 'commodity-futures-bot/1.0'})

    commodities = ['copper', 'crude-oil', 'gold', 'natural-gas']
    base_url = 'https://www.investing.com/commodities/'
    
    get_commodity_history(session, base_url, commodities)