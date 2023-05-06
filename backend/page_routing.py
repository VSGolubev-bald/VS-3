from flask import render_template, request, redirect, session, url_for, send_file
import backend.db as db
from backend.config import app
from io import BytesIO


@app.route('/pages')
def pages():
    current_user = db.getUser(session['username'])
    pagesList = db.getPages()
    return render_template('pages.html', pages=pagesList, user=current_user)


@app.route('/page/<tag>')
def page(tag: str):
    if not validateRead(tag):
        return render_template('403.html')
    current_user = db.getUser(session['username'])
    page_to_show = db.findPage(tag)
    return render_template('page_view.html', page=page_to_show, user=current_user)


@app.route('/delete_page/<tag>')
def delete_page(tag: str):
    if not validateWrite(tag):
        return render_template('403.html')
    db.deletePage(tag)
    return redirect(url_for('pages'))


@app.route('/download_file/<tag>/<file>')
def download_file(tag: str, file: str):
    if not validateRead(tag):
        return render_template('403.html')
    file_to_download = db.getFile(tag, file)
    return send_file(BytesIO(file_to_download['content']), download_name=file_to_download['filename'],
                     as_attachment=True)


@app.route('/add_page', methods=['POST', 'GET'])
def add_page():
    if not validateAdmin():
        return render_template('403.html')

    if request.method == 'GET':
        return render_template('add_page.html')

    tag = request.form['tag']
    if tag is None or tag == '':
        return 'Tag cannot be empty'
    owner = db.getUser(session['username'])['user_id']

    if db.findPage(tag) is not None:
        return "Page with tag '" + tag + "' already exists"

    db.insertPage(
        owner,
        tag,
        request.form['title'],
        request.form['description'],
        request.form['keywords'],
        request.form['body'],
        request.files.getlist('files')
    )
    return redirect(url_for('page', tag=tag))


@app.route('/edit_page/<tag>', methods=['GET', 'POST'])
def edit_page(tag):
    if not validateWrite(tag):
        return render_template('403.html')

    if request.method == 'GET':
        current_page = db.findPage(tag)
        curent_user = db.getUser(session['username'])
        all_users = list(map(lambda x: str(x['user_id']), db.getAllUsers()))
        read_users = db.getReadUsers(current_page['page_id'])
        write_users = db.getWriteUsers(current_page['page_id'])
        return render_template(
            'edit_page.html',
            user=curent_user,
            page=current_page,
            all_users=all_users,
            read_users=read_users,
            write_users=write_users
        )

    db.editPage(
        tag,
        request.form.get('title'),
        request.form.get('description'),
        request.form.get('keywords'),
        request.form.get('body'),
        request.files.getlist('files'),
        request.form.getlist('read_users[]'),
        request.form.getlist('write_users[]'),
    )

    return redirect(url_for('page', tag=tag))


@app.route('/delete_file/<tag>/<filename>')
def delete_file(tag: str, filename: str):
    if not validateWrite(tag):
        return render_template('403.html')

    db.deleteFile(tag, filename)
    return redirect(url_for('edit_page', tag=tag))


super_roles = list(map(lambda x: x.value, [db.Role.ADMIN, db.Role.EDITOR]))


def validateRead(tag: str) -> bool:
    current_user = db.getUser(session['username'])
    return current_user['account_type'] in super_roles \
        or db.validateReadAccess(tag, current_user['user_id'])


def validateWrite(tag: str) -> bool:
    current_user = db.getUser(session['username'])
    return current_user['account_type'] in super_roles \
            or db.validateWriteAccess(tag, current_user['user_id'])


def validateAdmin() -> bool:
    current_user = db.getUser(session['username'])
    return current_user['account_type'] == db.Role.ADMIN.value
