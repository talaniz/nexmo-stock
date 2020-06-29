import json
import os
import requests
import time
from urllib.parse import parse_qs

from alpha_vantage.timeseries import TimeSeries
from dotenv import load_dotenv
from flask import Flask, request
import nexmo
import redis
from rq import Queue

load_dotenv()

app = Flask(__name__)

r = redis.Redis()
q = Queue(connection=r)

client = nexmo.Client(application_id=os.getenv('APPLICATION_ID'),
                      private_key=os.getenv('PRIVATE_KEY_PATH'),)

def send_voice_call(msg, number):
    """Send the stock info to the recipient."""

    print("Calling {} with message {}".format(number, msg))
    ncco = [
        {
            'action': 'talk',
            'voiceName': 'Joey',
            'text': msg
        }
    ]

    response = client.create_call({
        'to': [{
            'type': 'phone',
            'number': number
        }],
        'from': {
            'type': 'phone',
            'number': os.getenv('NEXMO_PHONE_NUMBER')
        },
        'ncco': ncco
    })

    print(response)



def get_stock_symbol(query_string):
    """Search for a stock symbol using the text field provided in the query string."""

    QUERY_STRING = "https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={}&apikey={}"

    msg = query_string['text'][0]

    print("Processing request for: {}".format(msg))
    r = requests.get(QUERY_STRING.format(msg, os.getenv('ALPHA_VANTAGE_API')))
    matches = json.loads(r.content)['bestMatches']
    print(matches)
    best_match = matches[0]
    symbol = best_match['1. symbol']
    name = best_match['2. name']
    print("Found match for {}: {}".format(symbol, name))
    return symbol, name

def get_stock_data(symbol):
    """Get intraday stock data for the requested symbol."""

    ts = TimeSeries(key=os.getenv('ALPHA_VANTAGE_API'))
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
        # so the message isn't rushed
        msg += "<break time='45ms' /> {} <break time='30ms' /> {} <break time='45ms' />".format(
            k[2:], v)

    msg += "thank you for using the nexmo stock application. Goodbye.</speak>"
    return msg

def process_request(query_string):
    """ Function that returns len(n) and simulates a delay """

    query_string = parse_qs(query_string)
    phone_id = query_string['msisdn'][0]
    symbol, name = get_stock_symbol(query_string)
    stock_data = get_stock_data(symbol)
    voice_msg = "<speak>Hello, here is the requested information for {}".format(
        name)
    voice_msg += get_voice_message(stock_data)
    print(voice_msg)

    send_voice_call(voice_msg, phone_id)

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
    print("Enqueuing job with query string: {}".format(query_string))

    job = q.enqueue(process_request, query_string)

    print(f"Task {job.id} added to queue at {job.enqueued_at}")

    return 'OK'

if __name__ == "__main__":
    app.run()

