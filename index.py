"""nonempty"""
import os
import json
import requests
from flask import Flask, Response, request, jsonify

import pandas as pd
import numpy as np
#from statsmodels.tsa.arima.model import ARIMA


app = Flask(__name__)

URL ='https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'

headers = {'Content-Type': 'application/json',
          'Authorization': os.environ.get("API_KEY")}

URL ='https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'

@app.route("/", methods=["GET","POST"], defaults={'path': ''})
def home():
    """prediction"""
    if request.args.get('f'):
        forward_steps = int(request.args.get('f'))
    else:
        forward_steps =15
    if request.args.get('a'):
        address = request.args.get('a')
    else:
        address = "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"

    query = """
        {token (id: "%s"){tokenDayData { priceUSD date } } }
        """ % address

    r = requests.post(URL, json={'query': query})
    json_data = json.loads(r.text)
    df_data = json_data['data']['token']['tokenDayData']
    df = pd.DataFrame(df_data)

    #df.priceUSD = df.priceUSD.replace(0, np.nan).dropna()
    #df.priceUSD = df.priceUSD.astype(float)

    last = df.date.iloc[-1:].values[0]
    timestep = df.date.iloc[-1:].values[0]-df.date.iloc[-2:-1].values[0]

    return jsonify({ 'last_date': str(last), 'timestep': str(timestep)})
@app.route('/<path:path>')
def catch_all(path):
    """check"""
    return Response("<h1>Flask</h1><p>You visited: /%s</p>" % (path), mimetype="text/html")
