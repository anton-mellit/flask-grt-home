from flask import Flask, render_template, render_template_string, \
        flash, redirect, url_for, request, abort, send_file, \
        make_response

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

from flask_login import LoginManager, current_user, login_required
login_manager = LoginManager(app)

from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

from flask_mail import Mail
mail = Mail(app)

from flask_redis import FlaskRedis
redis = FlaskRedis(app)

from flaskext.markdown import Markdown
markdown = Markdown(app, extensions=['extra', 'mdx_math'],
        extension_configs={'mdx_math': {'enable_dollar_delimiter': True}})

from search import Search
search = Search(app)

from bleach import clean as bleach_clean
from bleach.sanitizer import ALLOWED_TAGS
@app.template_filter()
def bleach(s):
    return bleach_clean(s, tags=ALLOWED_TAGS+['p', 'pre', 'img'])

import json

@app.template_filter()
def json_encode(obj):
    return json.dumps(obj)

@app.template_filter()
def format_ical(s):
    res = []
    for line in s.split('\n'):
        for i in range((len(line)-1)//74 + 1):
            if i>0:
                res.append(' ')
            line_part = line[i*74:(i+1)*74]
            if line_part.strip():
                res.append(line_part+'\r\n')
    return ''.join(res)

@app.template_filter()
def modify_datetime(dt, **delta):
    return dt + timedelta(**delta)

from dateutil import tz
@app.template_filter()
def format_datetime(dt, format_string, timezone):
    return dt.astimezone(tz.gettz(timezone)).strftime(format_string)

@app.template_filter()
def format_date_ical(dt):
    return dt.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

import users
import pages
import events
import news
import playgrounds
import library

from datetime import datetime, timedelta, timezone

from itertools import islice

def url_for_self(**args):
    return url_for(request.endpoint, **dict(request.view_args, **args))

app.jinja_env.globals['url_for_self'] = url_for_self

@app.route('/news')
def news():
    return render_template('news/main.html', page=request.args.get('page'))

app.add_url_rule('/', 'index', news)

@app.route('/events/<past_or_future>')
@app.route('/events')
def events(past_or_future='future'):
    if past_or_future not in ('past', 'future'):
        abort(404)
    return render_template('events/main.html', \
            past_or_future=past_or_future, page=request.args.get('page'))

@app.route('/library')
def library():
    return render_template('library/main.html', page=request.args.get('page'))

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

@app.route('/calendar')
def calendar():
    response = make_response(render_template('calendar.ics'))
    response.headers['Content-Type'] = 'text/calendar; charset=utf=8'
    response.headers['Content-Disposition'] = 'attachment; filename=calendar.ics'
    return response


from html2text import HTML2Text
text_maker = HTML2Text()
text_maker.ignore_links = True

@app.route('/test-digest')
@login_required
def test_digest():
    msg_md = render_template('email/digest.md', user=current_user)
    html = render_template_string('{{ md | markdown }}', md=msg_md)
    body = text_maker.handle(html)
    return html + '<h1>Plain text:</h1><pre><code>' + body + '</code></pre>'

@app.route('/search')
def do_search():
    query = request.args.get('q', '')
    page = int(request.args.get('p', '0'))
    return search.search(query, page)


for f in (BASE_PATH / 'pages').iterdir():
    if f.suffix=='.md':
        def page_route():
            page = pages.load_page(f)
            return render_template('default.html', page=page)
        app.add_url_rule('/'+f.stem, f.stem, page_route)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
