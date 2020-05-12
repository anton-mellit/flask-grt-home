from run import app, config

from pages import EditPageForm, EditAttachmentsMixin

from flask_login import login_required

from wtforms import StringField, BooleanField, \
        SubmitField, TextAreaField
from wtforms.validators import DataRequired

import datetime

class NewLibraryForm(EditAttachmentsMixin):
    title = 'New library card'
    slug_field = 'talk_speaker'
    outer_class = 'large-form-container'
    layout = config['site']['layouts']['edit_library']
    talk_speaker = StringField('Speaker', validators=[DataRequired()])
    speaker_affiliation = StringField('Affiliation')
    talk_title = StringField('Title', validators=[DataRequired()])
    talk_location = StringField('Location')
    entered_date = StringField('Date', render_kw={'type':'date'})
    video = StringField('Video')
    content = TextAreaField('Abstract and other information')
    allow_comments = BooleanField('Allow registered users to leave comments?', default=True)
    submit = SubmitField('Save')

    def __init__(self):
        super().__init__('library')

    def populate_page(self, page, is_new):
        super().populate_page(page, is_new)
        page['date'] = page['date_created']
        if 'entered_date' in page:
            page['entered_date'] = datetime.date.fromisoformat(page['entered_date'])

class EditLibraryForm(NewLibraryForm):
    title = 'Edit library card'

@app.route('/edit-library/<post>', methods=['GET', 'POST'])
@app.route('/edit-library', methods=['GET', 'POST'])
@login_required
def edit_library(post=None):
    if post is not None:
        return EditLibraryForm().process_request(post)
    else:
        return NewLibraryForm().process_request(post)
