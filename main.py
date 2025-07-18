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
    history_df = load_df(commodity, 'historical')
    overview_df = load_df(commodity, 'overview')
    return history_df, overview_df

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )

@app.get("/futures/{commodity}", response_class=HTMLResponse)
async def get_commodity_data(request: Request, commodity: str):
    history_df, overview_df = load_commodity_data(commodity)

    hist_highest = history_df["High"].max()
    hist_lowest = history_df["Low"].min()
    hist_difference = hist_highest - hist_lowest
    hist_average = history_df["Price"].mean()

    history_json = history_df.to_json(orient='values')
    formatted_history_json = json.loads(history_json)
    overview_json = overview_df.to_json(orient='records', date_unit='s')
    formatted_overview_json = json.loads(overview_json)

    response_data =  {
        "commodity": commodity,
        "history": formatted_history_json,
        "history_columns": history_df.columns,
        "history_stats": {
            "highest": hist_highest,
            "lowest": hist_lowest,
            "difference": hist_difference,
            "average": hist_average
        },
        "overview": formatted_overview_json
    }

    return templates.TemplateResponse(
        request=request, name="futures.html", context=response_data
    )