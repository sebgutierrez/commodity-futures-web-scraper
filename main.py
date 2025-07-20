from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
from pathlib import Path
import json

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def load_df(commodity: str, type: str):
    df = None
    filename = f'{commodity}-{type}.pkl'
    path = Path.cwd() / commodity / filename
    if path.exists():
        df = pd.read_pickle(path)
    return df

def load_commodity_data(commodity: str):
    daily_history_df = load_df(commodity, 'daily-history')
    daily_overview_df = load_df(commodity, 'daily-overview')
    hourly_overview_df = load_df(commodity, 'hourly-overview')
    return daily_history_df, daily_overview_df, hourly_overview_df

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )

@app.get("/futures/{commodity}", response_class=HTMLResponse)
async def get_commodity_data(request: Request, commodity: str):
    daily_history_df, daily_overview_df, hourly_overview_df = load_commodity_data(commodity)

    daily_history_columns = list(daily_history_df.columns.values)
    daily_history_highest = round(float(daily_history_df["High"].max()), 4)
    daily_history_lowest = round(float(daily_history_df["Low"].min()), 4)
    daily_history_difference = round(float(daily_history_highest - daily_history_lowest), 4)
    daily_history_average = round(float(daily_history_df["Price"].mean()), 4)

    daily_history_json = daily_history_df.to_json(orient='values', indent=4)
    formatted_daily_history_data = json.loads(daily_history_json)

    daily_overview_columns = list(daily_overview_df.index.values)
    daily_overview_json = daily_overview_df.to_json(orient='values', indent=4)
    formatted_daily_overview_data = json.loads(daily_overview_json)

    hourly_overview_columns = list(hourly_overview_df['DateTime'].values)
    hourly_overview_data = list(hourly_overview_df['Last Price'].values)
    hourly_overview_date_time = hourly_overview_df['DateTime'].values[0]
    hourly_overview_last_price = float(hourly_overview_df['Last Price'].values[0])
    hourly_overview_price_change = round(float(hourly_overview_df['Price Change'].values[0]), 2)
    hourly_overview_price_change_percent = hourly_overview_df['Price Change Percent'].values[0]

    response_data = {
        "commodity": commodity,
        "daily_history": {
            "columns": daily_history_columns,
            "data": formatted_daily_history_data,
            "highest": daily_history_highest,
            "lowest": daily_history_lowest,
            "difference": daily_history_difference,
            "average": daily_history_average
        },
        "hourly_overview_chart": {
            "columns": hourly_overview_columns,
            "data": hourly_overview_data
        },
        "hourly_overview": {
            "date_time": hourly_overview_date_time,
            "last_price": hourly_overview_last_price,
            "price_change": hourly_overview_price_change,
            "price_change_percent": hourly_overview_price_change_percent
        },
        "daily_overview": {
            "columns": daily_overview_columns,
            "data": formatted_daily_overview_data,
        }
    }

    return templates.TemplateResponse(request=request, name="futures.html", context=response_data)