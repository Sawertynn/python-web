from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template("blog/index.html", posts=posts)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("blog.index"))


@bp.route("/<int:id>/single", methods=("GET", "POST"))
def single(id):
    """View single post"""

    post = get_post(id, check_author=False)
    return render_template("blog/single.html", post=post)


@bp.route("/<int:post_id>/like", methods=("POST",))
@login_required
def like(post_id):
    return react(post_id, g.user["id"], is_like=True)


@bp.route("/<int:post_id>/dislike", methods=("POST",))
@login_required
def dislike(post_id):
    return react(post_id, g.user["id"], is_like=False)


def react(post_id, user_id, is_like: bool):
    db = get_db()
    if request.method == "POST":
        old_like = db.execute(
            "SELECT is_like FROM reacts WHERE post_id = ? AND user_id = ?",
            (post_id, user_id),
        ).fetchone()
        if not old_like:
            db.execute(
                "INSERT INTO reacts (post_id, user_id, is_like) VALUES (?, ?, ?)",
                (post_id, user_id, is_like),
            )
            db.commit()
        elif old_like[0] != is_like:
            db.execute(
                "UPDATE reacts SET is_like = ? WHERE post_id = ? AND user_id = ?",
                (is_like, post_id, user_id),
            )
            db.commit()
    return redirect(url_for("blog.single", id=post_id))


def get_react(post_id, is_like: bool):
    count = (
        get_db()
        .execute(
            "SELECT COUNT(*) FROM reacts WHERE post_id = ? AND is_like = ?",
            (post_id, is_like),
        )
        .fetchone()[0]
    )
    return count
