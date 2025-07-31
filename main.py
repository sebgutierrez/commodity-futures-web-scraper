from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.gzip import GZipMiddleware
from fastapi_tailwind import tailwind
from contextlib import asynccontextmanager

import pandas as pd
from pathlib import Path
import jinja2
from jinja2.filters import FILTERS
import json

def datetime_formatting_filter(datetime_str, type="datetime"):
    format = ""
    if type == "datetime":
        format = '%b %d, %Y %H:%M %p'
        datetime_obj = datetime.fromisoformat(datetime_str)
        formatted_datetime = datetime.strftime(datetime_obj, format)
        return formatted_datetime
    else:
        original_format = "%m/%d/%Y %H:%M %p"
        new_format = '%b %d, %Y'
        datetime_object = datetime.strptime(datetime_str, original_format)
        formatted_date_string = datetime_object.strftime(new_format)
        return formatted_date_string

def split_range_string(range):
    values = range.split('-')
    return f"{values[0]} - {values[1]}"

FILTERS["datetime"] = datetime_formatting_filter
FILTERS["split"] = split_range_string

def hundredth_precision(float_str):
    split = float_str.split('.')
    if len(split[1]) > 1:
        hundredths = split[0] + '.' + split[1][:2] 
        return hundredths
    return float_str
    
static_files = StaticFiles(directory = "static")

@asynccontextmanager
async def lifespan(app: FastAPI):
    process = tailwind.compile(
        static_files.directory + "/output.css",
        tailwind_stylesheet_path = "./static/input.css"
    )
    yield # The code after this is called on shutdown
    process.terminate() # We must terminate the compiler on shutdown to
    # prevent multiple compilers running in development mode or when watch is enabled.

app = FastAPI(lifespan = lifespan)

app.mount("/static", static_files, name="static")
app.add_middleware(GZipMiddleware)

templates = Jinja2Templates(directory="templates")

def load_df(commodity: str, type: str):
    commodities_path = Path.cwd() / 'commodities'
    commodities_path.mkdir(exist_ok=True)
    commodity_path = commodities_path / commodity
    commodity_path.mkdir(exist_ok=True)
    df = None
    filename = f'{commodity}-{type}.pkl'
    df_path = commodity_path / filename
    if df_path.exists():
        df = pd.read_pickle(df_path)
    return df

def load_commodity_data(commodity: str):
    daily_history_df = load_df(commodity, 'daily-history')
    daily_overview_df = load_df(commodity, 'daily-overview')
    hourly_overview_df = load_df(commodity, 'hourly-overview')
    return daily_history_df, daily_overview_df, hourly_overview_df

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(request=request, name="about.html", context={"request": request})

@app.get("/futures/{commodity}", response_class=HTMLResponse)
async def get_commodity_data(request: Request, commodity: str):
    daily_history_df, daily_overview_series, hourly_overview_df = load_commodity_data(commodity)

    daily_history_columns = list(daily_history_df.columns.values)
    daily_history_highest = round(float(daily_history_df["High"].max()), 2)
    daily_history_lowest = round(float(daily_history_df["Low"].min()), 2)
    daily_history_difference = round(float(daily_history_highest - daily_history_lowest), 2)
    daily_history_average = round(float(daily_history_df["Price"].mean()), 2)

    daily_history_json = daily_history_df.to_json(orient='values', indent=4)
    formatted_daily_history_data = json.loads(daily_history_json)

    daily_overview_json = daily_overview_series.to_json(orient='index', indent=4)
    formatted_daily_overview_dict = json.loads(daily_overview_json)

    hourly_overview_timestamps = list(hourly_overview_df['Date Time'].values)
    hourly_overview_data = list(hourly_overview_df['Last Price'].values)
    hourly_overview_commodity_name = hourly_overview_df['Commodity Name'].values[0]

    hourly_overview_date_time = hourly_overview_df['Date Time'].values[0]
    hourly_overview_last_price = hundredth_precision(hourly_overview_df['Last Price'].values[0])
    hourly_overview_price_change = hundredth_precision(hourly_overview_df['Price Change'].values[0])
    hourly_overview_price_change_percent = hourly_overview_df['Price Change Percent'].values[0]

    previews = {}
    for cm in ["copper", "crude-oil", "gold", "natural-gas"]:
        if cm != commodity:
            df = load_df(cm, "hourly-overview")
            previews[cm] = {
                "commodity_name": cm,
                "commodity_full_name": df['Commodity Name'].values[0],
                "last_price": hundredth_precision(df['Last Price'].values[0]),
                "price_change_percent": df['Price Change Percent'].values[0]
            }

    response_data = {
        "commodity": hourly_overview_commodity_name,
        "daily_history": {
            "columns": daily_history_columns,
            "data": formatted_daily_history_data,
            "highest": daily_history_highest,
            "lowest": daily_history_lowest,
            "difference": daily_history_difference,
            "average": daily_history_average
        },
        "hourly_overview_chart": {
            "columns": hourly_overview_timestamps,
            "data": hourly_overview_data
        },
        "previews": previews,
        "hourly_overview": {
            "date_time": hourly_overview_date_time,
            "commodity_name": hourly_overview_commodity_name,
            "last_price": hourly_overview_last_price,
            "price_change": hourly_overview_price_change,
            "price_change_percent": hourly_overview_price_change_percent
        },
        "daily_overview": formatted_daily_overview_dict
    }

    return templates.TemplateResponse(request=request, name="futures.html", context=response_data)