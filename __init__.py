import json
from flask import Flask, session, abort, redirect, request, render_template
import pathlib
import os
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from google.oauth2 import id_token
from . import my_db, pb
import time
db = my_db.db
from .config import config

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = config.get("sql_alchemy_uri")
print(f'SQL {config.get("sql_alchemy_uri")}')

db.init_app(app)

web = config.get("web")
GOOGLE_CLIENT_ID = web['client_id']
print(f"GOOGLE_CLIENT_ID {GOOGLE_CLIENT_ID}")
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, ".secrets.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="https://sd3a.online/callback"
)

alive = 0
data = {}

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401) # Authorization required
        else:
            return function()
    return wrapper

@app.route("/")
def index():
    return "<a href = '/login'><button>Login with Google</button></a>"


@app.route("/protected_sensors")
@login_is_required
def protected_sensors():
    my_db.add_user_and_login(session['name'], session["google_id"])
    return render_template("protected_sensors.html", user_id=session['google_id'], online_users = my_db.get_all_logged_in_users())

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/logout")
def logout():
    my_db.user_logout(session['google_id'])
    session.clear()
    return redirect("/")

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response = request.url)

    if not session["state"] == request.args["state"]:
        abort(500) # State does not match! Don't trust this request.

    credentials = flow.credentials
    request_session = flow.authorized_session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session = cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token = credentials._id_token,
        request = token_request,
        audience = GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["google_token"] = credentials._id_token
    return redirect("/protected_sensors")

@app.route("/keep_alive")
def keep_alive():
    global alive, data
    alive += 1
    keep_alive_count = str(alive)
    data['keep_alive'] = keep_alive_count
    parsed_json = json.dumps(data)
    return str(parsed_json)

@app.route("/status=<name>-<action>", methods=["POST"])
def event(name, action):
    global data
    if name == "buzzer":
        if action == "on":
            data["alarm"] = True
        elif action == "off":
            data["alarm"] = False
    return str("Ok")


@app.route('/grant-<user_id>-<read>-<write>', methods=["POST"])
def grant_access(user_id, read, write):
    if session.get('google_id'):
        if session['google_id'] == config.get('admin_google_id'):
            print(f"Admin granting {user_id}-{read}-{write}")
            my_db.add_user_permission(user_id, read, write)
            if read == "true" and write == "true":
                token = pb.grant_read_write_access(user_id)
                my_db.add_token(user_id, token)
                access_response={'token':token, 'cipher_key':pb.cipher_key, 'uuid':user_id}
                return json.dumps(access_response)
            elif read == "true":
                token = pb.grant_read_access(user_id)
                my_db.add_token(user_id, token)
                access_response={'token':token, 'cipher_key':pb.cipher_key, 'uuid':user_id}
                return json.dumps(access_response)
            else:
                access_response = {'token':123, 'uuid':user_id, 'cipher_key':pb.cipher_key}
                return json.dumps(access_response)
        else:
            print("Non admin attempting to grant privileges")
            return json.dumps({"access":"denied"})
    else:
        print(f"Non-admin Granting {user_id}-{read}-{write}")
        my_db.add_user_permission(user_id, read, write)
        if read and write:
            token = pb.grant_read_write_access(user_id)
            my_db.add_token(user_id, token)
            access_response={'token':token, 'cipher_key':pb.cipher_key, 'uuid':user_id}
            return json.dumps(access_response)
        elif read:
            token = pb.grant_read_access(user_id)
            my_db.add_token(user_id, token)
            access_response={'token':token, 'cipher_key':pb.cipher_key, 'uuid':user_id}
            return json.dumps(access_response)
        else:
            access_response = {'token':123, 'uuid':user_id, 'cipher_key':pb.cipher_key}
            return json.dumps(access_response)



@app.route('/get_user_token', methods=["POST"])
def get_user_token():
    user_id = session['google_id']
    token = my_db.get_token(user_id)
    if token is not None:
        token = get_or_refresh_token(token)
        token_response = {'token':token}
    else:
        token_response = {'token':123, 'uuid':user_id, 'cipher_key':pb.cipher_key}
    return json.dumps(token_response)


def get_or_refresh_token(token):
    timestamp, ttl, uuid, read, write = pb.parse_token(token)
    current_time = time.time()
    if (timestamp + (ttl*60)) - current_time > 0:
        return token
    else:
        #The token has expired
        return grant_access(uuid, read, write)


@app.route('/get_device_token-<uuid>')
def get_device_token(uuid):
    token = my_db.get_token(uuid)
    if token is not None:
        token = get_or_refresh_token(token)
        token_response = {'token':token}
    else:
        token_response={'token':123}
    return json.dumps(token_response)


if __name__ == "__main__":
    app.run()
