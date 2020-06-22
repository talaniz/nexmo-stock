import json
import os
import requests
import time
from urllib.parse import parse_qs

from alpha_vantage.timeseries import TimeSeries
from flask import Flask, request
import nexmo
import redis
from rq import Queue


app = Flask(__name__)

r = redis.Redis()
q = Queue(connection=r)


def get_stock_symbol(query_string):
    """Search for a stock symbol using the text field provided in the query string."""

    QUERY_STRING = "https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={}&apikey={}"

    msg = query_string['text'][0]

    print("Processing request for: {}".format(msg))
    r = requests.get(QUERY_STRING.format(msg, os.environ['ALPHA_VANTAGE_API']))
    matches = json.loads(r.content)['bestMatches']
    print(matches)
    best_match = matches[0]
    symbol = best_match['1. symbol']
    name = best_match['2. name']
    print("Found match for {}: {}".format(symbol, name))
    return symbol, name

def get_stock_data(symbol):
    """Get intraday stock data for the requested symbol."""

    ts = TimeSeries(key=os.environ['ALPHA_VANTAGE_API'])
    data, _ = ts.get_intraday(symbol)

    dates = list(data.keys())
    dates.sort()
    latest = dates[-1]
    stock_data = data[latest]
    return stock_data

def get_voice_message(stock_data):
    """Take stock information and create a formatted voice message."""

    msg = ""
    for k, v in stock_data.items():
        msg += "{} {}".format(k[2:], v)

    return msg

def background_task(n):
    """ Function that returns len(n) and simulates a delay """

    delay = 2

    print("Task running")
    print(f"Simulating a {delay} second delay")

    time.sleep(delay)

    print(len(n))
    print("Task complete")

    return len(n)

@app.route("/task")
def index():

    if request.args.get("n"):

        job = q.enqueue(background_task, request.args.get("n"))

        return f"Task ({job.id} added to queue at {job.enqueued_at}"

    return "No value for count provided"

# Receive incoming events
@app.route("/answer", methods=['POST'])
def answer():
    """Handle inbound answer messages from Vonage."""

    print("called answer!")
    print(request.get_json())
    return 'OK'

@app.route("/event", methods=['POST'])
def event():
    """Handle inbound events for calls from Vonage."""

    print("called event!")
    print(request.get_json())
    return 'OK'


@app.route("/delivery", methods=['POST'])
def delivery():
    """Handle delivery events for texts from Vonage."""

    print("called delivery!")
    print(request.get_json())
    return 'OK'


@app.route("/inbound", methods=['POST'])
def inbound():
    """Handle inbound events for texts from Vonage."""

    print("called inbound!")
    query_string = request.get_data().decode('ascii')
    print("Message Request: {}".format(query_string))

    query_string = parse_qs(query_string)
    phone_id = query_string['msisdn']
    symbol, name = get_stock_symbol(query_string)
    stock_data = get_stock_data(symbol)
    voice_msg = "Hello, here is the requested information for {}".format(name)
    voice_msg += get_voice_message(stock_data)

    return 'OK'

if __name__ == "__main__":
    app.run()

