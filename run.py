from flask import Flask, render_template, render_template_string, flash, redirect, url_for, request, abort, send_file

app = Flask(__name__)

from pathlib import Path

BASE_PATH = Path(__file__).parent

import yaml

with (BASE_PATH / 'config.yaml').open() as f:
    config = yaml.safe_load(f)
    for key, value in config['flask'].items():
        app.config[key] = value

@app.context_processor
def inject_site():
    return { 'site': config['site'] }

from flask_login import LoginManager
login_manager = LoginManager(app)

from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

from flask_mail import Mail

mail = Mail(app)

from flaskext.markdown import Markdown

markdown = Markdown(app, extensions=['extra', 'mdx_math'], 
        extension_configs={'mdx_math': {'enable_dollar_delimiter': True}})

from bleach import clean as bleach_clean
from bleach.sanitizer import ALLOWED_TAGS
@app.template_filter()
def bleach(s):
    return bleach_clean(s, tags=ALLOWED_TAGS+['p', 'pre', 'img'])

import json

@app.template_filter()
def json_encode(obj):
    return json.dumps(obj)

import users
import pages
import events

from datetime import datetime, timedelta, timezone

from itertools import islice

def url_for_self(**args):
    return url_for(request.endpoint, **dict(request.view_args, **args))

app.jinja_env.globals['url_for_self'] = url_for_self

@app.route('/news')
def news():
    return render_template('news/main.html', page=request.args.get('page'))

@app.route('/news/<post>')
def news_item(post):
    item = pages.load_folder_item('data/news', post, 'item.md')
    if not item:
        abort(404)
    return render_template('news/item.html', item=item)

app.add_url_rule('/', 'index', news)

@app.route('/events/<past_or_future>')
@app.route('/events')
def events(past_or_future='future'):
    if past_or_future not in ('past', 'future'):
        abort(404)
    return render_template('events/main.html', \
            past_or_future=past_or_future, page=request.args.get('page'))

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

if __name__ == '__main__':
    app.run(host='0.0.0.0')

