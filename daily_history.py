from bs4 import BeautifulSoup as btfs
import pandas as pd
from pathlib import Path
import pickle
import pytz
import requests

def hundredth_precision(float_str):
	split = float_str.split('.')
	if len(split[1]) > 1:
		hundredths = split[0] + '.' + split[1][:2] 
		return hundredths
	return float_str

def strip_commas(string):
	stripped = ''
	for char in string:
		if char != ',':
			stripped += char
	return stripped

def save_history_df(df, filename, commodity):
	commodities_path = Path.cwd() / 'commodities'
	commodities_path.mkdir(exist_ok=True)
	commodity_path = commodities_path / commodity
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

		column_names.append('polarity')

		tbody = table.tbody

		historical_records = []
		for tr in tbody.find_all('tr'):
			historical_record = []
			polarity = ""
			for td in tr.find_all('td'):
				if td.time:
					historical_record.append(str(td.time['datetime']))
				elif td.string[-1] != 'K' and td.string[-1] != '%':
					if td.string.find(',') != -1:
						td.string = strip_commas(td.string)
					historical_record.append(float(hundredth_precision(td.string)))
				elif td.string[-1] == '%':
					if td.string[0] == '+':
						polarity = "+"
					else:
						polarity = "-"
					historical_record.append(str(td.string))
				else:
					historical_record.append(str(td.string))
			historical_record.append(polarity)
			# If historical data has been previously stored, only look for the latest day's data and stop the search early
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
		commodities_path = Path.cwd() / "commodities"
		commodity_path = commodities_path / commodity
		history_filename = f'{commodity}-daily-history.pkl'
		history_df_path = commodity_path / history_filename
		history_df = None
		if history_df_path.exists():
			history_df = scrape_historical_data(session, history_url, dataset_exists=True)
		else:
			history_df = scrape_historical_data(session, history_url)
		save_history_df(history_df, history_filename, commodity)

if __name__ == "__main__":
    session = requests.Session()
    session.headers.update({'User-Agent': 'commodity-futures-bot/1.0'})

    commodities = ['copper', 'crude-oil', 'gold', 'natural-gas']
    base_url = 'https://www.investing.com/commodities/'
    
    get_commodity_history(session, base_url, commodities)