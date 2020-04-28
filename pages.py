from run import BASE_PATH, app, config

import frontmatter
from users import load_user

from datetime import datetime

def load_file(path, slug):
    with path.open() as f:
        post = frontmatter.load(f)
    for key in list(post.keys()):
        if key in ('date', 'date_created', 'date_modified') and \
                isinstance(post[key], str) and post[key]:
            post[key] = datetime.fromisoformat(post[key])
    post['slug'] = slug
    return post

def save_file(path, post):
    with path.open('wb') as f:
        frontmatter.dump(post, f)

import re

def is_foldername(s):
    return re.match(config['foldername_regexp'], s)

def is_filename(s):
    return re.match(config['filename_regexp'], s)

def load_folder_item(folder, item, filename):
    if item and is_foldername(item) and not item.startswith('_'):
        return load_file(BASE_PATH / folder / item / filename, item)
    return None

def to_folder_name(name):
    name = name.strip()
    name = ''.join(ch if ch in '1234567890qwertyuioplkjhgfdsazxcvbnm' else '-' for ch in name.lower())
    if not name or name[0]=='-':
        name = 'x' + name
    return name

def new_folder_item(folder, name, filename):
    item = to_folder_name(name)
    path = BASE_PATH / folder / item
    if path.exists():
        i = 1
        while True:
            item2 = item + '-' + str(i)
            if not (BASE_PATH / folder / item2).exists():
                break
            i += 1
        item = item2
    return frontmatter.Post('', slug=item)

def save_folder_item(folder, filename, post):
    item = post['slug']
    if item and is_foldername(item) and not item.startswith('_'):
        if not (BASE_PATH / folder / item).exists():
            (BASE_PATH / folder / item).mkdir()
        save_file(BASE_PATH / folder / item / filename, post)

def save_folder_item_file(folder, item, file_to_save, filename, storage):
    if item and is_foldername(item) and not item.startswith('_'):
        if not (BASE_PATH / folder / item).exists():
            (BASE_PATH / folder / item).mkdir()
        storage.save(BASE_PATH / folder / item / file_to_save)

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
        if begin_date and post['date'] < begin_date:
            continue
        if end_date and post['date'] > end_date:
            continue
        yield post

@app.template_filter()
def sort_by_date(it, desc=False):
    return sorted(it, key=lambda post: post['date'], reverse=True if desc else False)

from itertools import islice

@app.template_filter()
def first_n(it, n):
    return islice(it, 0, n)

@app.template_filter()
def user_fullname(username):
    if username:
        user = load_user(username)
        if user:
            return user.data['fullname']
    return None

from datetime import datetime, timedelta, timezone

def handle_timedelta(dt):
    if isinstance(dt, dict):
        dt = timedelta(**dt)
        dt = datetime.now(timezone.utc) + dt
    return dt


class PageCollection:
    def __init__(self, folder, filename, params):
        self.folder = folder
        self.filename = filename
        self.params = params
        self.load()
    def load(self):
        items = load_folder(self.folder, self.filename)
        params = self.params
        if params.get('begin_date') or params.get('end_date'):
            items = date_between(items, 
                    handle_timedelta(params.get('begin_date')), 
                    handle_timedelta(params.get('end_date')))
        items = sort_by_date(items, params.get('desc'))
        if params.get('first_n'):
            items = first_n(items, params.get('first_n'))
        self.items = list(items)
        self.length = len(self.items)
        if params.get('pagination'):
            self.per_page = params.get('pagination')
            self.npages = (self.length-1)//self.per_page + 1
    def page(self, i):
        return self.items[i*self.per_page:(i+1)*self.per_page]


@app.context_processor
def inject_pages():
    res = {}
    for key, params in config['site']['collections'].items():
        # Force early binding
        def factory(params=params):
            return PageCollection(params['folder'], params['filename'], params)
        res[key] = factory
    return res



#@app.template_filter()
#def pagination_marks(size, max_num):
#    ln
