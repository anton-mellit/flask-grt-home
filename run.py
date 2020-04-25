from flask import Flask, render_template, render_template_string, flash, redirect, url_for, request

app = Flask(__name__)

from pathlib import Path

BASE_PATH = Path(__file__).parent

import yaml

with (BASE_PATH / 'config.yaml').open() as f:
    config = yaml.safe_load(f)
    for key, value in config['flask'].items():
        app.config[key] = value

from flask_login import LoginManager
login_manager = LoginManager(app)

from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

from flask_mail import Mail

mail = Mail(app)

from flaskext.markdown import Markdown

markdown = Markdown(app)

import users

@app.route('/news')
def news():
    page = { 'menu_item': 'news' }
    return render_template('body.html', config=config, page=page)

app.add_url_rule('/', 'index', news)

@app.route('/events')
def events():
    page = { 'menu_item': 'events' }
    return render_template('body.html', config=config, page=page)

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

if __name__ == '__main__':
    app.run(host='0.0.0.0')

