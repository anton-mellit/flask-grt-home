from flask import url_for, render_template

from run import BASE_PATH, config, app

from whoosh.fields import *

from whoosh.index import create_in, open_dir, exists_in

from pages import PageCollection

from whoosh.qparser import QueryParser

schema = Schema(url=ID(stored=True), date=DATETIME(stored=True),
    seminar=TEXT(stored=True), talk_speaker=TEXT(stored=True),
    title=TEXT(stored=True), talk_title=TEXT(stored=True), content=TEXT(stored=True))

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
                if field in item.metadata:
                    doc[field] = item.metadata[field]
                    if isinstance(field_type, TEXT):
                        content.append(doc[field])
            doc['url'] = url
            content.append(item.content)
            doc['content'] = ' '.join(content)
            writer.add_document(**doc)

    def reindex(self):
        for key, params in self.config['collections'].items():
            col = PageCollection(params['folder'], params['filename'], params)
            for item in col.items:
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
