from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db

bp = Blueprint("react", __name__)


@bp.route("/<int:post_id>/like", methods=("POST",))
@login_required
def like(post_id):
    return react(post_id, g.user["id"], is_like=True)


@bp.route("/<int:post_id>/dislike", methods=("POST",))
@login_required
def dislike(post_id):
    return react(post_id, g.user["id"], is_like=False)


def react(post_id, user_id, is_like: bool):
    if request.method == "POST":
        id = (
            get_db()
            .execute(
                "SELECT id FROM reacts WHERE post_id = ? AND user_id = ?",
                (post_id, user_id),
            )
            .fetchone()
        )
        if not id:
            get_db().execute(
                "INSERT INTO reacts (post_id, user_id, is_like) VALUES (?, ?, ?)",
                (post_id, user_id, is_like),
            )
    return redirect(url_for("blog.single", id=post_id))


def get_react(post_id, is_like: bool):
    count = (
        get_db()
        .execute(
            "SELECT COUNT(id) FROM reacts WHERE post_id = ? AND is_like = ?",
            (post_id, is_like),
        )
        .fetchone()
    )
    return count
