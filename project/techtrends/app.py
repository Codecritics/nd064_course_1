import sqlite3
import logging

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from os import environ
from werkzeug.exceptions import abort

NUMBER_OF_SQLITE_CONNECTIONS = 0


def log(type: str, hostname=None):
    log = logging.getLogger(type)
    log.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()

    if type == "werkzeug":
        log_format = f'%(levelname)s:%(name)s: %(asctime)s | : %(message)s'
        log_msg = ""
    else:
        log_format = f'%(levelname)s:%(name)s: %(asctime)s | : %(message)s'
        log_msg = ""

    console_handler.setFormatter(logging.Formatter(log_format))
    log.addHandler(console_handler)
    log.info('test')


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global NUMBER_OF_SQLITE_CONNECTIONS

    connection = sqlite3.connect('database.db')
    NUMBER_OF_SQLITE_CONNECTIONS += 1
    connection.row_factory = sqlite3.Row
    return connection


# Function to get a post using its ID
def get_post(post_id):
    global NUMBER_OF_SQLITE_CONNECTIONS

    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    NUMBER_OF_SQLITE_CONNECTIONS = NUMBER_OF_SQLITE_CONNECTIONS - 1 if NUMBER_OF_SQLITE_CONNECTIONS > 0 \
        else NUMBER_OF_SQLITE_CONNECTIONS
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('SECRET_KEY')
log = logging.getLogger("werkzeug")
log.disabled = True


# Define the main route of the web application
@app.route('/')
def index():
    global NUMBER_OF_SQLITE_CONNECTIONS

    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    NUMBER_OF_SQLITE_CONNECTIONS = NUMBER_OF_SQLITE_CONNECTIONS - 1 if NUMBER_OF_SQLITE_CONNECTIONS > 0 \
        else NUMBER_OF_SQLITE_CONNECTIONS
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        return render_template('404.html'), 404
    else:
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    return render_template('about.html')


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/healthz', methods=('GET',))
def health():
    return jsonify({'result': 'OK - healthy'}), 200


@app.route('/metrics', methods=('GET',))
def metrics():
    global NUMBER_OF_SQLITE_CONNECTIONS

    connection = get_db_connection()
    posts = connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    connection.close()

    return jsonify({'post_count': posts, 'db_connection_count': NUMBER_OF_SQLITE_CONNECTIONS}), 200


# start the application on port 3111
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='3111')
