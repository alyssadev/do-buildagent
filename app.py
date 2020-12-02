#!/usr/bin/env python3
from flask import Flask, request, render_template, redirect, url_for, session
from digital_ocean_client import DigitalOceanClient, ApiError
import requests
from os import environ
from random import choice
from string import ascii_letters, digits, punctuation
from datetime import datetime

client = DigitalOceanClient(environ["DO_OAUTH_CID"], environ["DO_OAUTH_CS"], domain="https://buildagent.alyssasmith.id.au")

app = Flask(__name__)
app.secret_key = "".join(choice(ascii_letters + digits + punctuation) for _ in range(32))

def check_token():
    if not "expiry" in session or not "token" in session:
        return False
    if "refresh_token" in session and session["expiry"] < datetime.now():
        token, scope, expiry, refresh_token = client.refresh_oauth_token(session["refresh_token"])
        session["token"] = token
        session["scope"] = scope
        session["expiry"] = expiry
        session["refresh_token"] = refresh_token
    return True

@app.route('/', methods=['GET'])
def index():
    error = request.args.get('error', None)
    if check_token():
        headers = {"Authorization": f"Bearer {session['token']}"}
        api_droplet_list_url = "https://api.digitalocean.com/v2/droplets"

        servers = requests.get(api_droplet_list_url, headers=headers,
                               timeout=3).json()
        return render_template(
            'server_list.html',
            servers=servers.get('droplets', None)
        )
    else:
        return render_template(
            'index.html',
            oauth_url=client.get_authorize_oauth_url(),
            error=error
        )

@app.route('/login', methods=['GET'])
def login():
    code = request.args.get('code', None)
    error = None
    if code:
        try:
            token, scope, expiry, refresh_token = client.finish_oauth(code)
            session["token"] = token
            session["scope"] = scope
            session["expiry"] = expiry
            session["refresh_token"] = refresh_token
        except ApiError as e:
            error = f'API Error: {e}'
        except TypeError as e:
            error = f'Error: {e}'
    return redirect(url_for('.index', error=error))

@app.route('/logout', methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for('.index'))

if __name__ == "__main__":
    app.run(port=25123, debug=True)
