import logging
import sqlite3
from datetime import datetime
from os import environ
from time import sleep

from flask import Flask, jsonify, render_template, request, url_for, redirect, flash, Response
from werkzeug.serving import WSGIRequestHandler
from werkzeug.urls import uri_to_iri

NUMBER_OF_SQLITE_CONNECTIONS = 0
time = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')


def custom_log_request(self, code="-", size="-"):
    try:
        path = uri_to_iri(self.path)
        msg = "%s %s %s" % (self.command, path, self.request_version)
    except AttributeError:
        msg = self.requestline
    code = str(code)
    werkzeug_logger.info(
        '%s - - [%s] "%s" %s %s' % (self.address_string(), self.log_date_time_string(), msg, code, size))


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

logging.basicConfig(level=logging.DEBUG, format=f'%(levelname)s:%(name)s:%(message)s', datefmt='%Y/%m/%d, %H:%M:%S')
werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.setLevel(logging.DEBUG)
WSGIRequestHandler.log_request = custom_log_request


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
        response = Response(render_template('404.html'), 404)
    else:
        response = Response(render_template('post.html', post=post))

    @response.call_on_close
    def on_close():
        sleep(1)
        if post is None:
            app.logger.info(f' {time} A non-existing article is accessed')
        else:
            app.logger.info(f' {time} Article "{post["content"]}" retrieved!')

    return response


# Define the About Us page
@app.route('/about')
def about():
    response = Response(render_template('about.html'))

    @response.call_on_close
    def on_close():
        sleep(1)
        app.logger.info(f'{time} The "About Us" page is retrieved')

    return response


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

            response = Response(redirect(url_for('index')))

    response = Response(render_template('create.html'))

    @response.call_on_close
    def on_close():
        sleep(1)
        app.logger.info(f'{time} A new article is created. With title {title}')

    return response


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
