import json

with open("/var/www/FlaskApp/FlaskApp/.secrets.json") as config_file:
    config = json.load(config_file)
