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

import users
import pages

from datetime import datetime, timedelta, timezone

from itertools import islice

def sidebar_events():
    items = pages.load_folder('data/events', 'myevent.md')
    items = pages.date_between(items, \
                datetime.now(timezone.utc) - timedelta(hours=1),
                None)
    items = pages.sort_by_date(items)
    return islice(items, 0, 5)


@app.route('/news')
def news():
    items = pages.load_folder('data/news', 'item.md')
    return render_template('news/main.html', items=items, events=sidebar_events())

@app.route('/news/<post>')
def news_item(post):
    item = pages.load_folder_item('data/news', post, 'item.md')
    if not item:
        abort(404)
    return render_template('news/item.html', item=item, events=sidebar_events())

app.add_url_rule('/', 'index', news)

@app.route('/events/<past_or_future>')
@app.route('/events')
def events(past_or_future='future'):
    if past_or_future not in ('past', 'future'):
        abort(404)
    items = pages.load_folder('data/events', 'myevent.md')
    if past_or_future=='future':
        items = pages.date_between(items, \
                datetime.now(timezone.utc) - timedelta(hours=1),
                None)
    else:
        items = pages.date_between(items, \
                None,
                datetime.now(timezone.utc))

    return render_template('events/main.html', \
            past_or_future=past_or_future, items=items)

@app.route('/event/<post>/')
def events_item(post):
    item = pages.load_folder_item('data/events', post, 'myevent.md')
    if not item:
        abort(404)
    return render_template('events/item.html', item=item)

@app.route('/event/<post>/<fname>')
def events_item_file(post, fname):
    path = pages.load_folder_item_file('data/events', post, fname, 'myevent.md')
    if not path:
        abort(404)
    return send_file(path)

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

if __name__ == '__main__':
    app.run(host='0.0.0.0')

