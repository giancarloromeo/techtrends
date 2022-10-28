"""This module contains the TechTrends application."""
import logging
import sqlite3

from contextlib import contextmanager
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort


app = Flask(__name__)
app.config["SECRET_KEY"] = "your secret key"


class DBAdapter:
    """The DB Adapter."""
    def __init__(self, database):
        self.database = database
        self.connections = 0

    @contextmanager
    def connect(self):
        """Connects to the database."""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        self.connections += 1
        yield conn
        conn.close()


    def create_post(self, title, content):
        """Creates a new post with the specified title and content.

        Args:
            - title: the post title
            - content: the post content
        """
        with self.connect() as conn:
            conn.execute("INSERT INTO posts (title, content) VALUES (?, ?)", (title, content))
            conn.commit()


    def get_post(self, post_id):
        """Gets a post with the specified ID.

        Returns:
            the post with the specified ID
        """
        with self.connect() as conn:
            res = conn.execute("SELECT * FROM posts WHERE id = ?;", (post_id,)).fetchone()
        return res


    def get_posts(self):
        """Gets all the posts.

        Returns:
            all the posts
        """
        with self.connect() as conn:
            res = conn.execute("SELECT * FROM posts;").fetchall()
        return res


    def get_posts_count(self):
        """Gets the total amount of posts.

        Returns:
            the total amount of posts
        """
        with self.connect() as conn:
            res = conn.execute("SELECT COUNT() FROM posts;").fetchone()[0]
        return res


db = DBAdapter("database.db")


@app.route("/")
def index():
    """Renders the Main page of the web application."""
    return render_template("index.html", posts=db.get_posts())


@app.route("/<int:post_id>")
def post(post_id):
    """Renders an individual Post page."""
    res = db.get_post(post_id)
    if res is None:
        app.logger.error("Article wih ID '%d' does not exist!", post_id)
        return render_template("404.html"), 404 # page not found

    app.logger.info("Article '%s' retrieved!", res["title"])
    return render_template("post.html", post=res)


@app.route("/about")
def about():
    """Renders the About page."""
    app.logger.info("About page retrieved!")
    return render_template("about.html")


@app.route("/create", methods=("GET", "POST"))
def create():
    """Handles the Post creation request."""
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if not title:
            flash("Title is required!")
        else:
            db.create_post(title, content)
            app.logger.info("Article '%s' created!", title)

            return redirect(url_for("index"))

    return render_template("create.html")


@app.route("/healthz")
def healthz():
    """Returns the health status."""

    try:
        db.get_posts_count()    # get posts count to check the DB

        res = app.response_class(
            response=json.dumps({"result": "OK - healthy"}),
            status=200,
            mimetype="application/json"
        )
    except sqlite3.OperationalError as err:
        app.logger.error("error: %s", err)
        res = app.response_class(
            response=json.dumps({"result": "ERROR - unhealthy"}),
            status=500,
            mimetype="application/json"
        )

    return res


@app.route("/metrics")
def metrics():
    """Returns the metrics."""
    res = app.response_class(
        response=json.dumps({"db_connection_count": db.connections,
            "post_count": db.get_posts_count()
        }),
        status=200,
        mimetype="application/json"
    )
    return res


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

    app.run(host="0.0.0.0", port="3111")
