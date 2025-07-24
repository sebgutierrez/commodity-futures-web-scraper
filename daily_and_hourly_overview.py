from bs4 import BeautifulSoup as btfs
from datetime import date, datetime, timezone
import pandas as pd
from pathlib import Path
import pickle
import pytz
import requests

def has_been_a_day():
	commodity_path = Path.cwd() / 'copper'
	commodity_path.mkdir(exist_ok=True)
	daily_series_path = commodity_path / 'copper-daily-overview.pkl'
	if daily_series_path.exists():
		loaded_series = pd.read_pickle(daily_series_path)
		last_recorded_date = datetime.strptime(loaded_series[0]['Date Time'], "%m/%d/%Y %I:%M %p").date()
		todays_date = datetime.today().date()
		if todays_date > last_recorded_date:
			return True 
		else:
			return False
	# To not prevent creating of file
	return True

def save_data(daily_series, hourly_df, commodity, has_been_a_day):
	commodity_path = Path.cwd() / commodity
	commodity_path.mkdir(exist_ok=True)
	hourly_df_path = commodity_path / f'{commodity}-hourly-overview.pkl'

	if hourly_df_path.exists():
		loaded_df = pd.read_pickle(hourly_df_path)
		concatenated_df = pd.concat([hourly_df, loaded_df])
		if concatenated_df.shape[0] > 96:
			concatenated_df = concatenated_df[:96] 
		concatenated_df.to_pickle(hourly_df_path)
	else:
		hourly_df.to_pickle(hourly_df_path)

	if daily_series is not None and has_been_a_day:
		daily_series_path = commodity_path / f'{commodity}-daily-overview.pkl'
		daily_series.to_pickle(daily_series_path)

def scrape_overview_data(session, url, has_been_a_day):
	try:
		chicago_tz = pytz.timezone('America/Chicago')
		current_time_chicago = datetime.now(pytz.utc).astimezone(chicago_tz)
		formatted_isoformat = current_time_chicago.isoformat()
		formatted_datetime = current_time_chicago.strftime("%m/%d/%Y %I:%H %p")

		response = session.get(url)
		response.raise_for_status() 
		soup = btfs(response.text, 'html.parser')

		header_data = []
		commodity_name = soup.find('div', class_={'flex flex-col gap-6 md:gap-0'}).div.div.div.h1.text.strip()
		header_data.append(str(commodity_name))
		header_details = soup.find('div', attrs={'data-test': 'instrument-header-details'})
		price_last = header_details.find('div', attrs={'data-test': 'instrument-price-last'}).text.strip()
		header_data.append(str(price_last))
		price_change = header_details.find('span', attrs={'data-test': 'instrument-price-change'}).text.strip()
		header_data.append(str(price_change))
		price_change_percent = ''
		for string in header_details.find('span', attrs={'data-test': 'instrument-price-change-percent'}).strings:
			if string == '(' or string == '%)':
				continue
			price_change_percent += string
		price_change_percent += '%'
		header_data.append(str(price_change_percent))

		daily_series = None
		if has_been_a_day:
			daily_series_data = [formatted_datetime]
			daily_series_indices = ['Date Time', 'Prev. Close', 'Open', 'Day Range', '52 Week Range', 'Volume', '1-Year Change', 'Month', 'Contract Size', 'Settlement Day', 'Tick Value', 'Point Value', 'Last Rollover Day']
			dl_tag = soup.find('dl', class_={'sm:mr-8'})
			if dl_tag:
				for div in dl_tag.find_all('div', recursive=False):
					dd_tag = div.find('dd')
					if dd_tag and 'data-test' in dd_tag.attrs:
						daily_series_data.append(str(dd_tag.text.strip()))
			second_dl_tag = soup.find('dl', class_={'sm:block'})
			if second_dl_tag:
				settlement_day = soup.find('dd', attrs={'data-test': 'settlement_date'}).text.strip()
				daily_series_data.append(settlement_day)
				tick_value = soup.find('dd', attrs={'data-test': 'tick_value'}).text.strip()
				daily_series_data.append(tick_value)
				point_value = soup.find('dd', attrs={'data-test': 'point_value'}).text.strip()
				daily_series_data.append(point_value)
				rollover_day = soup.find('dd', attrs={'data-test': 'rollover_day'}).text.strip()
				daily_series_data.append(rollover_day)
			daily_series = pd.DataFrame(data=daily_series_data, index=daily_series_indices)


		hourly_df_record = [formatted_isoformat] + header_data
		hourly_df_columns = ['Date Time', 'Commodity Name', 'Last Price', 'Price Change', 'Price Change Percent']
		hourly_df = pd.DataFrame(data=[hourly_df_record], columns=hourly_df_columns)
		return daily_series, hourly_df
	except requests.exceptions.HTTPError as e:
		print(f"HTTP Error: {e}")
	except requests.exceptions.RequestException as e:
		print(f"An error occurred: {e}")

def get_commodity_overview(session, base_url, commodities):
	has_been_a_day_flag = has_been_a_day()
	for commodity in commodities:
		overview_url = base_url + commodity
		daily_series, hourly_df = scrape_overview_data(session, overview_url, has_been_a_day_flag)
		save_data(daily_series, hourly_df, commodity, has_been_a_day_flag)

if __name__ == "__main__":
    session = requests.Session()
    session.headers.update({'User-Agent': 'commodity-futures-bot/1.0'})

    commodities = ['copper', 'crude-oil', 'gold', 'natural-gas']
    base_url = 'https://www.investing.com/commodities/'
    
    get_commodity_overview(session, base_url, commodities)