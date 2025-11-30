#!/bin/bash
if [ -f .env ]; then
    export $(cat .env | sed 's/#.*//g' | xargs)
fi
export FLASK_APP=backend/app.py
flask db migrate -m "Add model_path to Scan model"
flask db upgrade
