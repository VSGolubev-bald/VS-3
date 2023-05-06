from flask import Flask
from flask_avatars import Avatars
from flask_moment import Moment

app = Flask(__name__, template_folder='../templates')
app.secret_key = 'mysecretkey'
avatar = Avatars(app)
from datetime import datetime
moment = Moment(app)


def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(timestamp)

app.jinja_env.filters['timestamp_to_datetime'] = timestamp_to_datetime

