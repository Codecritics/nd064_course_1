import logging
import sqlite3
import sys
from os import environ
from flask_session import Session

from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect("database.db")
    app.config["DB_CONN_COUNTER"] += 1
    connection.row_factory = sqlite3.Row
    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = environ.get("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"
app.config["DB_CONN_COUNTER"] = 0
sess = Session(app)


# Define the main route of the web application
@app.route("/")
def index():
    connection = get_db_connection()
    posts = connection.execute("SELECT * FROM posts").fetchall()
    connection.close()

    return render_template("index.html", posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route("/<int:post_id>")
def post(post_id):
    post = get_post(post_id)

    if post is None:
        response = Response(render_template("404.html"), 404)
    else:
        response = Response(render_template("post.html", post=post))

    @response.call_on_close
    def on_close():
        if post is None:
            app.logger.info("A non-existing article is accessed")
        else:
            app.logger.info('Article "%s" retrieved!', post["content"])

    return response


# Define the About Us page
@app.route("/about")
def about():
    response = Response(render_template("about.html"))

    @response.call_on_close
    def on_close():
        app.logger.info(f'The "About Us" page is retrieved')

    return response


# Define the post creation functionality
@app.route("/create", methods=("GET", "POST"))
def create():
    title = None
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if not title:
            response = Response(flash("Title is required!"))
        else:
            connection = get_db_connection()
            connection.execute(
                "INSERT INTO posts (title, content) VALUES (?, ?)", (title, content)
            )
            connection.commit()
            connection.close()
            response = redirect(url_for("index"))
    else:
        response = Response(render_template("create.html"))

    @response.call_on_close
    def on_close():
        if title:
            app.logger.info(" A new article is created. With %s ", title)

    return response


@app.route("/healthz", methods=("GET",))
def health():
    return jsonify({"result": "OK - healthy"}), 200


@app.route("/metrics", methods=("GET",))
def metrics():
    connection = get_db_connection()
    posts = connection.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    connection.close()

    return (
        jsonify(
            {"post_count": posts, "db_connection_count": app.config["DB_CONN_COUNTER"]}
        ),
        200,
    )


# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format=f"%(levelname)s:%(name)s: %(asctime)s %(message)s ",
        datefmt="%Y/%m/%d, %H:%M:%S",
    )
    app.run(host="0.0.0.0", port="3111")
