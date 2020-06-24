# nexmo-stock
Send a text message to your registered Vonage phone number and receive a text-to-voice call with the latest
stock information. Handles webhooks to receive incoming text messages and outgoing phone call events.

## Prerequisites

Before installing, you will need the following:

A [new application](https://developer.nexmo.com/application/overview#creating-applications) from developer.nexmo.com with voice capabilities.

Configure a [new number](https://developer.nexmo.com/numbers/guides/number-management#rent-a-virtual-number) and link it to your application.

An [Alpha Advantage free API key](https://www.alphavantage.co/support/#api-key).

A running instance of [redis](https://redis.io/download).

    $ redis-server

For local development, [ngrok](https://ngrok.com/) running locally

    $ ngrok http 5000

## Set up

Fill in the .env-example file with the API information, private key, phone number and application ID, rename to .env.

Add event and answer URLs to your Vonage application:

* Add the `${NGROK_URL}/inbound` and `${NGROK_URL}/delivery` urls to your account in the [Default SMS Setting](https://dashboard.nexmo.com/settings).

* Add the `${NGROK_URL}/answer` and `${NGROK_URL}/event` urls to your application settings under voice capabilities.

Clone the repository and create a python virtualenv

    $ git clone git@github.com:talaniz/vonage-stock.git && cd vonage-stock

Create a virtualenv and install requirements

    $ virtualenv -p $(which python3) nexmo-stock
    ...created virtual environment
    $ pip install -r requirements.txt

Start the rq worker application

    $ rq worker
    14:13:41 Worker rq:worker:afb23ac5ea4e4b129e8a9aea55c0a83f: started, version 1.4.2
    ...

In another terminal, start the application

    $ cd /path/to/nexmo-stock && source bin/activate
    $ export FLASK_APP=run.py
    $ export FLASK_ENV = development
    $ flask run
    * Serving Flask app "app.py" (lazy loading)
    ...

## Usage
Send a text to your configured number with a company name or publicly traded stock symbol and answer the call.