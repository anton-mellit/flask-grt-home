from run import app, config

from wtforms import StringField, BooleanField, \
        SubmitField, SelectField, TextAreaField, \
        MultipleFileField
from wtforms.validators import DataRequired, Regexp

from flask_login import login_required

from users import timezone_widget, timezone_choices
from pages import EditPageForm, EditAttachmentsMixin, DateField, \
    TimeField

from datetime import datetime, timezone
from dateutil import tz




duration_choices = list({ 'unknown': 'unknown',
                '30': '30 minutes',
                '15': '15 minutes',
                '45': '45 minutes',
                '60': '1 hour',
                '75': '1 hour 15 minutes',
                '90': '1 hour 30 minutes',
                '120': '2 hours',
                '180': '3 hours',
                '240': '4 hours',
                '360': '6 hours',
}.items())

class EventForm(EditPageForm):
    title = 'New event'
    slug_field = 'seminar'
    outer_class = 'large-form-container'
    layout = config['site']['layouts']['edit_event']
    seminar = StringField('Seminar, institution', validators=[DataRequired()])
    entered_date = DateField('Date', validators=[DataRequired()])
    entered_time = TimeField('Time', validators=[DataRequired()])
    entered_timezone = SelectField('Timezone', validators=[DataRequired()], \
            widget=timezone_widget, choices=timezone_choices)
    duration = SelectField('Duration', choices=duration_choices)
    talk_speaker = StringField('Speaker, affiliation')
    talk_title = StringField('Title')
    online_access = StringField('How to access?')
    online_secret = StringField('Secret (e.g. password, we show it only to registered users)')
    content = TextAreaField('Abstract and other information')
    allow_comments = BooleanField('Allow registered users to leave comments?', default=True)
    submit = SubmitField('Save')

    def __init__(self):
        super().__init__('events')

    def populate_page(self, page, is_new):
        super().populate_page(page, is_new)
        timezone = tz.gettz(self.entered_timezone.data)
        page['date'] = datetime.combine(self.entered_date.data, \
            self.entered_time.data).replace(tzinfo=timezone)
        page['entered_time'] = str(page['entered_time'])

class EventFormAttachments(EventForm, EditAttachmentsMixin):
    title = 'Edit event'


@app.route('/edit-event/<post>', methods=['GET', 'POST'])
@app.route('/edit-event', methods=['GET', 'POST'])
@login_required
def edit_event(post=None):
    if post is not None:
        return EventFormAttachments().process_request(post)
    else:
        return EventForm().process_request(post)
