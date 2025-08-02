#!/bin/bash

VENV_PATH="/home/ubuntu/commodity-futures-web-scraper/venv"

PYTHON_SCRIPT="/home/ubuntu/commodity-futures-web-scraper/daily_history.py"

source "$VENV_PATH/bin/activate"

python3 "$PYTHON_SCRIPT" /home/ubuntu/commodity-futures-web-scraper/commodities

deactivate