from bs4 import BeautifulSoup as btfs
import requests
import pandas as pd
from datetime import date

    ### General Overview
    # https://www.investing.com/commodities/crude-oil
    #h2 = soup.find('h2')

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
    commodities = ['crude-oil', 'natural-gas', 'copper', 'gold']
    for commodity in commodities:
        base_url = 'https://www.investing.com/commodities/'
        history_url = base_url + commodity + '-historical-data'
        df = request_historical_data(session, history_url)
        filename = f'{commodity}-historical-{date.today()}.pkl'
        df.to_pickle(filename)

session = requests.Session()
session.headers.update({'User-Agent': 'commodity-futures-bot/1.0'})

get_commodity_history(session)
