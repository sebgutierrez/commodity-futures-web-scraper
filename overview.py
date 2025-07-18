from bs4 import BeautifulSoup as btfs
from datetime import date, datetime, timezone
import pandas as pd
from pathlib import Path
import pickle
import pytz
import requests

def convert_military_to_meridian(military_time_str):
	dt_object = datetime.strptime(military_time_str, "%H:%M")
	meridian_time_str = dt_object.strftime("%I:%M %p")
	return meridian_time_str

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

def scrape_overview_data(session, url):
	try:
		chicago_tz = pytz.timezone('America/Chicago')
		current_time = datetime.now(chicago_tz)
		military_time = ""
		if current_time.hour < 10:
			military_time += "0"
		military_time += str(current_time.hour) + ':' + str(current_time.minute)
		meridian_time = convert_military_to_meridian(military_time)

		response = session.get(url)
		response.raise_for_status() 
		soup = btfs(response.text, 'html.parser')

		header_details = soup.find('div', attrs={'data-test': 'instrument-header-details'})

		header_data = []
		price_last = header_details.find('div', attrs={'data-test': 'instrument-price-last'}).string
		header_data.append(str(price_last))
		price_change = header_details.find('span', attrs={'data-test': 'instrument-price-change'}).text
		header_data.append(str(price_change))
		price_change_percent = ''
		for string in header_details.find('span', attrs={'data-test': 'instrument-price-change-percent'}).strings:
			if string == '(' or string == '%)':
				continue
			price_change_percent += string
		price_change_percent += '%'
		header_data.append(str(price_change_percent))

		dl_info = [meridian_time] + header_data
		dl_tag = soup.find('dl')

		if dl_tag:
			for div in dl_tag.find_all('div', recursive=False):
				dd_tag = div.find('dd')
				if dd_tag and 'data-test' in dd_tag.attrs:
					dl_info.append(str(dd_tag.text.strip()))

		columns = ['Current Time', 'Last Price', 'Price Change', 'Price Change Percent', 'Prev. Close', 'Open', 'Day Range', '52 Week Range', 'Volume', '1-Year Change', 'Month', 'Contract Size']
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

    commodities = ['copper', 'crude-oil', 'gold', 'natural-gas']
    base_url = 'https://www.investing.com/commodities/'
    
    get_commodity_overview(session, base_url, commodities)