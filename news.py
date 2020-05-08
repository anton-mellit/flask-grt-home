from run import app, config
from wtforms import StringField, BooleanField, \
        SubmitField, TextAreaField
from wtforms.validators import DataRequired
from pages import EditAttachmentsMixin
from flask_login import login_required

class NewsForm(EditAttachmentsMixin):
    title = 'New post'
    slug_field = 'post_title'
    outer_class = 'large-form-container'
    post_title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content')
    allow_comments = BooleanField('Allow registered users to leave comments?', default=True)
    submit = SubmitField('Save')
    layout = config['site']['layouts']['edit_news']

    def __init__(self):
        super().__init__('news')

    def init_edit(self, page):
        page['post_title'] = page['title']
        super().init_edit(page)


    def populate_page(self, page, is_new):
        super().populate_page(page, is_new)
        if 'date' not in page:
            if 'date_created' not in page:
                page['date_created'] = page['date_modified']
            page['date'] = page['date_created']
        page['title'] = page['post_title']

class NewsFormEdit(NewsForm):
    title = 'Edit post'

@app.route('/edit-news/<post>', methods=['GET', 'POST'])
@app.route('/edit-news', methods=['GET', 'POST'])
@login_required
def edit_news(post=None):
    if post is not None:
        return NewsFormEdit().process_request(post)
    else:
        return NewsForm().process_request(post)
