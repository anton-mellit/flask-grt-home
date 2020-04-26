from run import BASE_PATH, app, config

import frontmatter
from users import load_user

from datetime import datetime

def load_file(path, slug):
    with path.open() as f:
        post = frontmatter.load(f)
    for key in list(post.keys()):
        if key in ('date', 'date_created', 'date_modified') and \
                isinstance(post[key], str):
            if post[key]:
                post[key] = datetime.fromisoformat(post[key])
            else:
                print('Missing date:', slug)
    post['slug'] = slug
    return post

import re

def is_foldername(s):
    return re.match(config['foldername_regexp'], s)

def is_filename(s):
    return re.match(config['filename_regexp'], s)

def load_folder_item(folder, item, filename):
    if item and is_foldername(item) and not item.startswith('_'):
        return load_file(BASE_PATH / folder / item / filename, item)
    return None

def load_folder_item_file(folder, item, file_to_get, filename):
    if file_to_get == filename:
        return None
    if item and is_foldername(item) and not item.startswith('_'):
        folder = BASE_PATH / folder / item
        if folder.is_dir():
            lst = [path for path in folder.iterdir() if path.name==file_to_get]
            if lst:
                return lst[0]
    return None

def load_folder(folder, filename):
    for path in (BASE_PATH / folder).iterdir():
        if path.is_dir() and not path.name.startswith('_'):
            yield load_file(path / filename, path.name)

@app.template_filter()
def date_between(it, begin_date, end_date):
    for post in it:
        print(post['date'], begin_date)
        if begin_date and post['date'] < begin_date:
            continue
        if end_date and post['date'] > end_date:
            continue
        yield post

@app.template_filter()
def sort_by_date(it, desc=False):
    return sorted(it, key=lambda post: post['date'], reverse=desc)

@app.template_filter()
def user_fullname(username):
    if username:
        user = load_user(username)
        if user:
            return user.data['fullname']
    return None



#@app.template_filter()
#def pagination_marks(size, max_num):
#    ln
