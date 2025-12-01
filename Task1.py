Part 1 — Backend (all files for comments CRUD + tests)

File 1 — app/models/comment.py

# app/models/comment.py
from datetime import datetime
from app.db import db  # adapt if your project exposes SQLAlchemy instance at a different path

class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # relationship - back_populates assumes Task defines `comments`
    task = db.relationship("Task", back_populates="comments")

File 2 — (If needed) update app/models/task.py to include relationship

# app/models/task.py
# Add the `comments` relationship if it doesn't already exist
# Keep other Task fields as-is in your template

# ... existing imports ...
from app.db import db

class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    # ... your other fields (title, description, etc.) ...

    # Add this relationship if missing:
    comments = db.relationship(
        "Comment",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

File 3 — app/api/comments_routes.py

# app/api/comments_routes.py
from flask import Blueprint, request, jsonify
from app.db import db
from app.models.comment import Comment
from app.models.task import Task
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint("comments", __name__, url_prefix="/api")

def comment_to_dict(c: Comment):
    return {
        "id": c.id,
        "task_id": c.task_id,
        "body": c.body,
        "author": c.author,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None
    }

@bp.route("/tasks/<int:task_id>/comments", methods=["GET"])
def get_comments(task_id):
    # returns list of comments for a task
    task = Task.query.get_or_404(task_id)
    comments = Comment.query.filter_by(task_id=task.id).order_by(Comment.created_at.asc()).all()
    return jsonify([comment_to_dict(c) for c in comments]), 200

@bp.route("/tasks/<int:task_id>/comments", methods=["POST"])
def create_comment(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json() or {}
    body = (data.get("body") or "").strip()
    author = data.get("author")
    if not body:
        return jsonify({"error": "body is required"}), 400

    comment = Comment(task_id=task.id, body=body, author=author)
    try:
        db.session.add(comment)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "database error"}), 500

    return jsonify(comment_to_dict(comment)), 201

@bp.route("/comments/<int:comment_id>", methods=["PUT", "PATCH"])
def update_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    data = request.get_json() or {}
    if "body" not in data:
        return jsonify({"error": "body is required"}), 400
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "body cannot be empty"}), 400

    comment.body = body
    if "author" in data:
        comment.author = data.get("author")
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "database error"}), 500

    return jsonify(comment_to_dict(comment)), 200

@bp.route("/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    try:
        db.session.delete(comment)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "database error"}), 500
    return jsonify({"message": "deleted"}), 200

File 4 — Register blueprint in your app factory (e.g., app/__init__.py or app/app.py)

# app/__init__.py  (or wherever your create_app factory is)
from flask import Flask
from app.db import db, init_db  # adapt to your project's db init functions
# ... other imports ...

def create_app(config_object=None):
    app = Flask(__name__, static_folder=None)
    # load config if passed
    if config_object:
        app.config.from_mapping(config_object)
    else:
        app.config.from_pyfile("config.py", silent=True)

    # initialize db
    db.init_app(app)
    # flask-migrate initialization if used can go here

    # register other blueprints
    from app.api.comments_routes import bp as comments_bp
    app.register_blueprint(comments_bp)

    # ... register other blueprints ...

    return app

File 5 — Tests: tests/test_comments.py

# tests/test_comments.py
import pytest
from app import create_app
from app.db import db as _db
from app.models.task import Task
from app.models.comment import Comment
import json

@pytest.fixture
def app():
    config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    }
    app = create_app(config)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def create_task(title="Test Task"):
    t = Task()
    # adapt if Task requires fields e.g., title/description
    # If Task model requires a title field:
    try:
        t.title = title
    except Exception:
        pass
    _db.session.add(t)
    _db.session.commit()
    return t

def test_create_comment_success(client, app):
    with app.app_context():
        task = create_task()
        res = client.post(f"/api/tasks/{task.id}/comments", json={"body": "This is a comment", "author": "Yug"})
        assert res.status_code == 201
        data = res.get_json()
        assert data["body"] == "This is a comment"
        assert data["task_id"] == task.id
        assert data["author"] == "Yug"

def test_create_comment_missing_body(client, app):
    with app.app_context():
        task = create_task()
        res = client.post(f"/api/tasks/{task.id}/comments", json={})
        assert res.status_code == 400
        data = res.get_json()
        assert "error" in data

def test_update_comment_success(client, app):
    with app.app_context():
        task = create_task()
        res = client.post(f"/api/tasks/{task.id}/comments", json={"body": "initial"})
        assert res.status_code == 201
        comment = res.get_json()
        cid = comment["id"]

        res2 = client.put(f"/api/comments/{cid}", json={"body": "updated"})
        assert res2.status_code == 200
        data = res2.get_json()
        assert data["body"] == "updated"

def test_update_comment_missing_body_field(client, app):
    with app.app_context():
        task = create_task()
        res = client.post(f"/api/tasks/{task.id}/comments", json={"body": "text"})
        cid = res.get_json()["id"]

        res2 = client.put(f"/api/comments/{cid}", json={})
        assert res2.status_code == 400

def test_delete_comment(client, app):
    with app.app_context():
        task = create_task()
        res = client.post(f"/api/tasks/{task.id}/comments", json={"body": "to delete"})
        cid = res.get_json()["id"]

        res2 = client.delete(f"/api/comments/{cid}")
        assert res2.status_code == 200

        # deleting again should return 404
        res3 = client.delete(f"/api/comments/{cid}")
        assert res3.status_code == 404

File 6 — app/db.py (if your template doesn't already provide db init; otherwise skip)

# app/db.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)

Extra: requirements additions (if not present)

Flask
Flask-SQLAlchemy
pytest
# if using Flask-Migrate:
Flask-Migrate

Notes / where to place files

Put comment.py under your models package/location.

Put comments_routes.py under your API/blueprints folder.

Ensure the create_app in your project imports and registers the blueprint as shown.

If your Task model requires certain fields on creation, adapt create_task() in tests to supply them (e.g., Task(title="x")).



---

Part 2 — Frontend (all files for comments UI)

Place these React components in your frontend src (e.g., src/components/comments/). Minimal dependencies; uses the browser Fetch API.

File 1 — src/components/comments/CommentForm.jsx

// src/components/comments/CommentForm.jsx
import React, { useState, useEffect } from "react";

export default function CommentForm({ onSubmit, initial = { body: "", author: "" }, onCancel, submitLabel = "Submit" }) {
  const [body, setBody] = useState(initial.body || "");
  const [author, setAuthor] = useState(initial.author || "");

  useEffect(() => {
    setBody(initial.body || "");
    setAuthor(initial.author || "");
  }, [initial]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = (body || "").trim();
    if (!trimmed) return alert("Comment body is required");
    onSubmit({ body: trimmed, author: (author || "").trim() || null });
    // reset when adding (but avoid clearing when editing)
    if (!onCancel) {
      setBody("");
      setAuthor("");
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: "8px" }}>
      <div>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Write a comment..."
          rows={3}
          style={{ width: "100%", padding: "8px" }}
        />
      </div>
      <div style={{ marginTop: "6px" }}>
        <input
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
          placeholder="Your name (optional)"
          style={{ width: "100%", padding: "8px" }}
        />
      </div>
      <div style={{ marginTop: "8px" }}>
        <button type="submit">{submitLabel}</button>
        {onCancel && (
          <button type="button" onClick={onCancel} style={{ marginLeft: "8px" }}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
  }
