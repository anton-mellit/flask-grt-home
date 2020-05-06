from run import BASE_PATH, app, config, markdown

from flask import request, render_template, flash, redirect, url_for, \
    send_file, jsonify

from flask_login import current_user, login_required

from pages import PageFolder
import json

@app.route('/playgrounds/<post>/')
@login_required
def playgrounds_item(post):
    item = load_folder_item('data/playgrounds', post, 'index.md')
    if not item:
        abort(404)
    if current_user.get_id() not in item['usernames']:
        abort(403)
    return render_template('playgrounds/item.html', item=item)

@app.route('/playgrounds/<post>/<username>', methods=['POST'])
@login_required
def playgrounds_update(post, username):
    item = load_folder_item('data/playgrounds', post, 'index.md')
    if not item:
        abort(404)
    if (username!=current_user.get_id()):
        abort(403)
    if current_user.get_id() not in item['usernames']:
        abort(403)
    envelope = json.loads(request.form['payload'])
    print(envelope)
    update_chunk_id = envelope['update_chunk']
    update_content = envelope['content'].strip()
    remote_chunks = envelope['chunks']
    print(item.metadata)
    chunks = item.metadata['chunks']
    chunk_ids = [chunk['id'] for chunk in chunks]
    print('Chunk ids:', chunk_ids)
    if update_chunk_id not in chunk_ids:
        i = remote_chunks.index(update_chunk_id)
        i -= 1
        while i>=0 and remote_chunks[i] not in chunk_ids:
            i -= 1
        j = chunk_ids.index(remote_chunks[i])+1 if i>=0 else 0
        chunks.insert(j, {'id': update_chunk_id})
    else:
        j = chunk_ids.index(update_chunk_id)
    print('Setting data:', j, chunks)
    chunks[j]['content'] = update_content
    if not update_content:
        chunks.pop(j)
    html = markdown(update_content)
    save_folder_item('data/playgrounds', 'index.md', item)

    return jsonify({'content': html})
