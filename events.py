from run import app, config

from flask import request, render_template, flash, redirect, url_for, send_file

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, \
        SubmitField, SelectField, TextAreaField, \
        MultipleFileField
from wtforms.validators import DataRequired, Regexp
from wtforms.fields.html5 import DateField, TimeField

from flask_login import current_user, login_required

from users import timezone_widget, timezone_choices, flash_errors
from pages import load_folder_item, load_folder_item_file, \
        new_folder_item, save_folder_item, save_folder_item_file

from datetime import datetime, timezone
from dateutil import tz

import json

from werkzeug.utils import secure_filename

def datetime_now():
    return datetime.now(timezone.utc)

@app.route('/event/<post>/')
def events_item(post):
    item = load_folder_item('data/events', post, 'myevent.md')
    if not item:
        abort(404)
    return render_template('events/item.html', item=item)

@app.route('/event/<post>/<fname>')
def events_item_file(post, fname):
    path = load_folder_item_file('data/events', post, secure_filename(fname), 'myevent.md')
    if not path:
        abort(404)
    return send_file(path)

duration_choices = list({ 'unknown': 'unknown',
                '15': '15 minutes',
                '30': '30 minutes',
                '45': '45 minutes',
                '60': '1 hour',
                '75': '1 hour 15 minutes',
                '90': '1 hour 30 minutes',
                '120': '2 hours',
                '180': '3 hours',
                '240': '4 hours',
                '360': '6 hours',
}.items())

class DropzoneField(StringField):
    def __init__(self, title, options={}, **kw):
        super(StringField, self).__init__(title, **kw)
        self.options = options

class EventForm(FlaskForm):
    outer_class = 'large-form-container'
    layout = config['site']['layouts']['edit_event']
    seminar = StringField('Seminar, institution', validators=[DataRequired()])
    entered_date = StringField('Date', validators=[DataRequired()], render_kw={'type':'date'})
    entered_time = StringField('Time', validators=[DataRequired()], render_kw={'type':'time'})
    entered_timezone = SelectField('Timezone', validators=[DataRequired()], \
            widget=timezone_widget, choices=timezone_choices)
    duration = SelectField('Duration', choices=duration_choices)
    talk_speaker = StringField('Speaker, affiliation')
    talk_title = StringField('Title')
    online_access = StringField('How to access?')
    online_secret = StringField('Secret (e.g. password, we show it only to registered users)')
    content = TextAreaField('Abstract and other information')
    allow_comments = BooleanField('Allow registered users to leave comments?', default=True)
    attachments = DropzoneField('Upload attachments here')
    submit = SubmitField('Save')


@app.route('/edit-event/<post>', methods=['GET', 'POST'])
@app.route('/edit-event', methods=['GET', 'POST'])
@login_required
def edit_event(post=None, action=None):
    print(request.args)
    print(request.form)
    print(request.files)
    if post is not None:
        item = load_folder_item('data/events', post, 'myevent.md')
        if not item:
            flash('You are not authorized to edit this page', 'error')
            return redirect(url_for('events_item', post=post))
        if item['username']!=current_user.get_id():
            flash('You are not authorized to edit this page', 'error')
            return redirect(url_for('events_item', post=post))
    action = request.args.get('_action')
    if action:
        return edit_event_action(post, action)
    elif request.method=='GET':
        if post is not None:
            form = EventForm(data=item.metadata)
            form.content.data = item.content
            attachments = list(item['attachments'])
            for att in attachments:
                att['url'] = url_for('events_item_file', post=post, fname=att['name'])
            form.attachments.data = json.dumps(attachments)
        else:
            form = EventForm()
    else:
        form = EventForm()
        if form.validate_on_submit():
            data = form.data
            if post is None:
                item = new_folder_item('data/events', data['seminar'], 'myevent.md') 
                item['username'] = current_user.get_id()
                item['date_created'] = datetime_now()
            else:
                item['date_modified'] = datetime_now()

            item['attachments'] = json.loads(data['attachments'])
            for attachment in item['attachments']:
                attachment['name'] = secure_filename(attachment['name'])

            for key in ['seminar', 'entered_date', 'entered_time', 'entered_timezone',
                    'duration', 'talk_speaker', 'talk_title', 'online_access', 'online_secret',
                    'allow_comments']:
                if key in data:
                    item[key] = data[key]
            item.content = data['content']
            timezone = tz.gettz(data['entered_timezone'])
            item['date'] = datetime.strptime('%s %s' % \
                    (data['entered_date'], data['entered_time']), 
                    '%Y-%m-%d %H:%M').replace(tzinfo=timezone)

            save_folder_item('data/events', 'myevent.md', item)
            if post:
                flash('Your chages have been saved.', 'success')
            else:
                flash('Event has been created.', 'success')
            #except e:
            #    flash('Errors occured. Event could not be saved.', 'error')
            return redirect(url_for('events_item', post=item['slug']))
    flash_errors(form)
    return render_template('medium-form.html', form=form)

def edit_event_action(post, action):
    if action=='upload':
        for f in request.files.values():
            save_folder_item_file('data/events', post, secure_filename(f.filename), 'myevent.md', f)
    print('Called')
    print(action)
    return 'OK'

