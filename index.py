"""nonempty"""
from os.path import join
import json
from datetime import datetime
import requests
from flask import Flask, request, jsonify, send_file
import joblib
import pandas as pd

app = Flask(__name__)

URL ='https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'

FORWARD_STEPS = 10

def get_data(address):
    """
    queries the data for the token

    address: address of the Uniswap contract
    """

    query = f"""
        {{token (id: "{address}"){{tokenDayData(first:1000, skip:2) {{ priceUSD date open close high low volume volumeUSD}} }} }}
    """
    response = requests.post(URL, json={'query': query}, timeout=7.5)
    json_data = json.loads(response.text)
    data = json_data['data']['token']['tokenDayData']
    out_df = pd.DataFrame(data)

    return out_df


def input_cells(latest_date, steps=FORWARD_STEPS):
    """
    outputs cells that we use to input predictions
    """
    empty_predictions = pd.DataFrame({'date':[n*86400+latest_date for n in range(1, steps+1)]})
    return empty_predictions


def time_features(df):
    """generate time features"""
    df["utc"] = df.date.apply(lambda x: datetime.utcfromtimestamp(x))
    df['day'] = df.utc.apply(lambda time: time.day)
    df["weekday"] = df.utc.apply(lambda time: time.dayofweek)
    df['month'] = df.utc.apply(lambda time: time.month)
    df['year'] = df.utc.apply(lambda time: time.year).astype("category")
    return df

@app.route("/", methods=["GET","POST"])
def home():
    """prediction"""
    if request.args.get('a'):
        address = request.args.get('a')
    else:
        address = "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"

    df_data = get_data(address)
    empty_predictions = input_cells(df_data.date.values[-1:][0])
    df_all = pd.concat([df_data, empty_predictions]).reset_index(drop=True)
    df_withfeatures = time_features(df_all)

    columns = ['open', 'close', 'high', 'low', 'volume', 'volumeUSD']
    for column in columns:
        df_withfeatures[column] = df_withfeatures[column].shift(FORWARD_STEPS)

    features = ['priceUSD', 'date', 'open', 'close', 'high', 'low', 'volume',
       'volumeUSD', 'day', 'weekday', 'month', 'year']

    df_withfeatures = df_withfeatures.iloc[-FORWARD_STEPS:][features]


    #for column in ['day', 'weekday', 'month', 'year']:
    #    df_all[column] = df_all[column].astype(int)

    return df_withfeatures.to_html(header="true", table_id="table")
