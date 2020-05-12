from run import BASE_PATH, app, config, redis
from flask import render_template, send_file, abort, request, flash, redirect, \
    url_for
from users import load_user, flash_errors
from flask_wtf import FlaskForm
from wtforms import StringField
from flask_login import current_user
from werkzeug.utils import secure_filename as w_secure_filename

import frontmatter
from datetime import date, datetime, timedelta, timezone
import re
import itertools
import json

try:
    import cPickle as pickle
except ImportError:
    import pickle

def secure_filename(s):
    print(s)
    s = w_secure_filename(s)
    if not s:
        s = 'x'
    return s

def load_page(path):
    with path.open() as f:
        page = frontmatter.load(f).to_dict()
    for key in list(page.keys()):
        if key in ('date', 'date_created', 'date_modified') and \
                isinstance(page[key], str) and page[key]:
            page[key] = datetime.fromisoformat(page[key])
        if key == 'entered_date' and page[key]:
            page[key] = date.fromisoformat(page[key])
    if 'username' not in page.keys():
        if 'taxonomy' in page.keys() and 'author' in page['taxonomy']:
            page['username'] = page['taxonomy']['author'][0]
    return page

def save_page(path, page):
    post = frontmatter.Post(**page)
    with path.open('wb') as f:
        frontmatter.dump(post, f)

class PageFolder:
    def __init__(self, params):
        self.folder = params['folder']
        self.filename = params['filename']
        self.params = params
        if 'caching' in params:
            self.caching_enabled = True
            self.cache_fields = params['caching']['fields']
        else:
            self.caching_enabled = False

    def load_page(self, slug, cached=False):
        if slug==secure_filename(slug):
            if cached and self.caching_enabled:
                key = self.folder+'/'+slug
                page = redis.get(key)
                if page:
                    page = pickle.loads(page)
                    page['slug'] = slug
                    return page
            try:
                page = load_page(BASE_PATH / self.folder / slug / self.filename)
            except FileNotFoundError:
                return None
            page['slug'] = slug
            if cached and self.caching_enabled:
                self.save_page_cache(page)
            return page
        return None

    def save_page_cache(self, page):
        page_small = {}
        for field in self.cache_fields:
            if field in page:
                page_small[field] = page[field]
        key = self.folder+'/'+page['slug']
        redis[key] = pickle.dumps(page_small)

    def new_page(self, slug_suggestion):
        slug0 = secure_filename(slug_suggestion).lower()
        for slug in itertools.chain((slug0,), \
                (('%s-%d') % (slug0, i) for i in itertools.count(1))):
            path = BASE_PATH / self.folder / slug
            if not path.exists():
                break
        return {'slug': slug}

    def save_page(self, page):
        slug = page['slug']
        if slug==secure_filename(slug):
            if not (BASE_PATH / self.folder / slug).exists():
                (BASE_PATH / self.folder / slug).mkdir()
            save_page(BASE_PATH / self.folder / slug / self.filename, page)
            if self.caching_enabled:
                self.save_page_cache(page)
                redis.delete(self.folder)

    def delete_page(self, slug):
        if slug==secure_filename(slug):
            if (BASE_PATH / self.folder / slug).is_dir():
                for f in (BASE_PATH / self.folder / slug).iterdir():
                    f.unlink()
                (BASE_PATH / self.folder / slug).rmdir()
            if self.caching_enabled:
                redis.delete(self.folder)

    def save_media(self, slug, filename, storage):
        filename = secure_filename(filename)
        if filename==self.filename:
            filename += 'x'
        if slug==secure_filename(slug):
            if not (BASE_PATH / self.folder / slug).exists():
                (BASE_PATH / self.folder / slug).mkdir()
            storage.save(BASE_PATH / self.folder / slug / filename)

    def move_media(self, slug, filename, path_from):
        filename = secure_filename(filename)
        if filename==self.filename:
            filename += 'x'
        if slug==secure_filename(slug):
            if not (BASE_PATH / self.folder / slug).exists():
                (BASE_PATH / self.folder / slug).mkdir()
            path_from.replace(BASE_PATH / self.folder / slug / filename)

    def load_media(self, slug, filename):
        filename = secure_filename(filename)
        if filename==self.filename:
            filename += 'x'
        if slug==secure_filename(slug):
            return BASE_PATH / self.folder / slug / filename

    def pages(self, cached=False):
        print('Folder', self.folder)
        slugs = None
        if self.caching_enabled:
            slugs = redis.get(self.folder)
            if slugs:
                slugs = pickle.loads(redis[self.folder])
        if not slugs:
            slugs = []
            for path in (BASE_PATH / self.folder).iterdir():
                if path.is_dir() and not path.name.startswith('_'):
                    slugs.append(path.name)
            if self.caching_enabled:
                redis.set(self.folder, pickle.dumps(slugs))
        for slug in slugs:
            yield self.load_page(slug, cached)



def datetime_now():
    return datetime.now(timezone.utc)

def handle_timedelta(dt):
    if dt and isinstance(dt, dict):
        dt = timedelta(**dt)
        dt = datetime.now(timezone.utc) + dt
    return dt

@app.template_filter()
def date_between(it, begin_date, end_date):
    begin_date = handle_timedelta(begin_date)
    end_date = handle_timedelta(end_date)
    for page in it:
        if begin_date and page['date'] < begin_date:
            continue
        if end_date and page['date'] > end_date:
            continue
        yield page

@app.template_filter()
def sort_by_date(it, desc=False):
    return sorted(it, key=lambda page: page['date'], reverse=True if desc else False)

@app.template_filter()
def first_n(it, n):
    return itertools.islice(it, 0, n)


class PageCollection:
    def __init__(self, folder, params):
        self.folder = folder
        self.params = params
        self.load()
    def load(self):
        params = self.params
        pages = self.folder.pages(params.get('cached', False))
        if params.get('begin_date') or params.get('end_date'):
            pages = date_between(pages, params.get('begin_date'),
                    params.get('end_date'))
        pages = sort_by_date(pages, params.get('desc'))
        if params.get('first_n'):
            pages = first_n(pages, params.get('first_n'))
        self.pages = list(pages)
        self.length = len(self.pages)
        if params.get('pagination'):
            self.per_page = params.get('pagination')
            self.npages = (self.length-1)//self.per_page + 1
    def page(self, i):
        return self.pages[i*self.per_page:(i+1)*self.per_page]



folders = {}
for key, params in config['site']['folders'].items():
    folder = PageFolder(params)
    folders[key] = folder
    if params['routes']:
        def render_page(post, folder=folder, template=params['template']):
            page = folder.load_page(post)
            if not page:
                abort(404)
            return render_template(template, item=page)
        def render_media(post, fname, folder=folder):
            path = folder.load_media(post, fname)
            if not path:
                abort(404)
            return send_file(path)
        for route in params['routes']:
            app.add_url_rule(route+"/<post>/", key+"_item", render_page)
            app.add_url_rule(route+"/<post>/<fname>", key+"_item_file", render_media)


@app.context_processor
def inject_pages():
    res = {}
    for key, params in config['site']['collections'].items():
        # Force early binding
        def factory(params=params):
            return PageCollection(folders[params['folder']], params)
        res[key] = factory
    return res


class EditPageForm(FlaskForm):
    MESSAGE_UNAUTHORIZED = 'You are not authorized to edit this page'
    MESSAGE_SUCCESS_NEW = 'New page has been created.'
    MESSAGE_SUCCESS_EDIT = 'Your changes have been saved.'

    excluded_fields = ['csrf_token']

    def __init__(self, folder):
        super().__init__()
        self.folder = folder
        self.actions = {}

    def user_can_edit(self, user, page):
        return page['username']==user or load_user(user).data.get('editor')==True

    def init_edit(self, page):
        self.process(data=page)

    def init_create(self):
        pass

    def render(self):
        return render_template('medium-form.html', form=self)

    slug_field = 'title'

    def create_new_page(self):
        return folders[self.folder].new_page(self[self.slug_field].data)

    def populate_page(self, page, is_new):
        for field in self:
            if field.name not in self.excluded_fields:
                page[field.name] = field.data
        page['date_modified'] = datetime_now()
        if is_new:
            page['username'] = current_user.get_id()
            page['date_created'] = page['date_modified']

    def process_save(self, page, is_new):
        self.populate_page(page, is_new)
        folders[self.folder].save_page(page)

    def process_request(self, post):
        print(request.args)
        print(request.form)
        print(request.files)
        if post is not None:
            page = folders[self.folder].load_page(post)
            if not page:
                abort(404)
            if not self.user_can_edit(current_user.get_id(), page):
                flash('You are not authorized to edit this page', 'error')
                return redirect(url_for(self.folder+'_item', post=post))
        action = request.args.get('_action')
        if action:
            if action in self.actions:
                return self.actions[action](post)
            abort(400)
        if request.method=='GET':
            if post is not None:
                self.init_edit(page)
            else:
                self.init_create()
        else:
            if self.validate_on_submit():
                is_new = post is None
                if is_new:
                    page = self.create_new_page()
                self.process_save(page, is_new)
                if post:
                    flash(self.MESSAGE_SUCCESS_EDIT, 'success')
                else:
                    flash(self.MESSAGE_SUCCESS_NEW, 'success')
                return redirect(url_for(self.folder+'_item', post=page['slug']))
        flash_errors(self)
        return self.render()


class DropzoneField(StringField):
    def __init__(self, title, options={}, **kw):
        super(StringField, self).__init__(title, **kw)
        self.options = options

import uuid

class EditAttachmentsMixin(EditPageForm):
    attachments = DropzoneField('Upload attachments here')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions['upload'] = self.upload

    def redis_key(self, store):
        return 'store-owner/'+store

    def upload(self, post):
        for f in request.files.values():
            store = request.form.get('store')
            print('store', store)
            if store:
                if redis.get(self.redis_key(store)).decode()!=current_user.get_id():
                    abort(403)
                folders['tmp'].save_media(store, secure_filename(f.filename), f)
            else:
                if post:
                    folders[self.folder].save_media(post, secure_filename(f.filename), f)
                else:
                    abort(400)
        return 'OK'

    def init_create(self):
        store = folders['tmp'].new_page(str(uuid.uuid4()))['slug']
        self.attachments.store = store
        self.attachments.data = json.dumps([])
        redis.set(self.redis_key(store), current_user.get_id())

    def init_edit(self, page):
        super().init_edit(page)
        attachments = page.get('attachments', [])
        for att in attachments:
            att['url'] = url_for(self.folder+'_item_file', post=page['slug'], fname=att['name'])
        self.attachments.data = json.dumps(attachments)
        self.attachments.store = ''

    def populate_page(self, page, is_new):
        super().populate_page(page, is_new)
        page['attachments'] = json.loads(self.attachments.data)

    def process_save(self, page, is_new):
        super().process_save(page, is_new)
        if is_new:
            store = request.form.get('store')
            if secure_filename(store)!=store:
                abort(400)
            if not redis.get(self.redis_key(store)):
                abort(403)
            if redis.get(self.redis_key(store)).decode()!=current_user.get_id():
                abort(403)
            for att in page['attachments']:
                original_path = folders['tmp'].load_media(store, att['name'])
                folders[self.folder].move_media(page['slug'], att['name'], original_path)
            folders['tmp'].delete_page(store)
            redis.delete(self.redis_key(store))


        #for attachment in page['attachments']:
        #    attachment['name'] = secure_filename(attachment['name'])
