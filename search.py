from flask import url_for, render_template

from run import BASE_PATH, config, app

from whoosh.fields import *

from whoosh.index import create_in, open_dir, exists_in

from pages import PageCollection, folders

from whoosh.qparser import QueryParser

import datetime

schema = Schema(url=ID(stored=True, unique=True), date=DATETIME(stored=True),
    seminar=TEXT(stored=True), talk_speaker=TEXT(stored=True),
    title=TEXT(stored=True), talk_title=TEXT(stored=True), talk_location=TEXT(stored=True),
    speaker_affiliation=TEXT(stored=True), entered_date=DATETIME(stored=True),
    content=TEXT(stored=True))

def date_to_datetime(dt):
    return datetime.datetime.combine(dt, datetime.time())

class Search:
    def __init__(self, app):
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        self.config = config['search']
        path = self.config['index']
        if exists_in(path):
            self.index = open_dir(path)
        else:
            self.index = create_in(path, schema)
        self.pagination = int(self.config['pagination'])

    def index_item(self, url, item):
        with self.index.writer() as writer:
            doc = {}
            content = []
            for field, field_type in schema.items():
                if field in item:
                    doc[field] = item[field]
                    if isinstance(doc[field], datetime.date):
                        doc[field] = date_to_datetime(doc[field])
                    if isinstance(field_type, TEXT):
                        content.append(doc[field])
            if 'video' in item:
                content.append('video')
            doc['url'] = url
            content.append(item['content'])
            doc['content'] = ' '.join(content)
            print(item)
            print(doc)
            writer.update_document(**doc)

    def reindex(self):
        for key, params in self.config['collections'].items():
            col = PageCollection(folders[params['folder']], params)
            for item in col.pages:
                url = url_for(params['endpoint'], post=item['slug'])
                self.index_item(url, item)


    def search(self, query, page):
        query = QueryParser('content', schema).parse(query)
        with self.index.searcher() as searcher:
            results = searcher.search_page(query, page+1,
                pagelen=self.pagination)
            response = render_template('search.html', query=query, \
                results=results, page=page)
        return response



if __name__ == '__main__':
    import run

    with run.app.app_context():
        print('Reindexing')
        run.search.reindex()
