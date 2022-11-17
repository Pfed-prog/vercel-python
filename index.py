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
    df = pd.concat([df_data, empty_predictions]).reset_index(drop=True)

    columns = ['open', 'close', 'high', 'low', 'volume', 'volumeUSD']

    for x in columns:
        df[x] = df[x].shift(FORWARD_STEPS)

    df = df.dropna()

    print(df.head())

    # scale data
    #scaler = joblib.load(join("data",  'scaler.save'))
    y_scaler = joblib.load(join("data",  'y_scaler.save'))


    #df.iloc[:, 1:] = scaler.transform(df.iloc[:, 1:])
    df[['priceUSD']] = y_scaler.transform(df[['priceUSD']])

    #model = joblib.load(join("data",  'lstm.pkl'))


    #make prediction

    sequence_length = 110
    make_pred_data = df.iloc[-sequence_length:]
    make_pred_data = make_pred_data.values.reshape((1, sequence_length, 12))

    #prediction = model.predict(make_pred_data)
    last = df.date.iloc[-1:].values[0]

    return jsonify({ 'last_date': str(last)})


    #return jsonify({ 'last_date': str(last), "prediction": str(prediction) })

@app.route('/prediction')
def predict():
    """returns prediction"""
    predictions = joblib.load(join("data",  'model.pkl'))
    return jsonify({'predictions': list(predictions)})

@app.route('/return-files/')
def return_files_txt():
    """returns file"""
    return send_file(join("data",  'file.txt'))
