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

    daily_hist_highest = daily_history_df["High"].max()
    daily_hist_lowest = daily_history_df["Low"].min()
    daily_hist_difference = daily_hist_highest - daily_hist_lowest
    daily_hist_average = daily_history_df["Price"].mean()

    daily_history_json = daily_history_df.to_json(orient='values', indent=4)
    formatted_daily_history_json = json.loads(daily_history_json)

    daily_overview_json = daily_overview_df.to_json(orient='values', indent=4)
    formatted_daily_overview_json = json.loads(daily_overview_json)

    hourly_overview_json = hourly_overview_df.to_json(orient='values', date_unit='s', indent=4)
    formatted_hourly_overview_json = json.loads(hourly_overview_json)
    
    response_data =  {
        "commodity": commodity,
        "daily_history_columns": daily_history_df.columns,
        "daily_history_stats": {
            "highest": daily_hist_highest,
            "lowest": daily_hist_lowest,
            "difference": daily_hist_difference,
            "average": daily_hist_average
        },
        "daily_history": formatted_daily_history_json,
        "hourly_overview": formatted_hourly_overview_json,
        "daily_overview": formatted_daily_overview_json
    }

    return templates.TemplateResponse(
        request=request, name="futures.html", context=response_data
    )