# Better-Software-Task-1
✅ Task 1 — README (Backend: Comment CRUD APIs + Tests)

Task 1: Backend Comment CRUD APIs (Flask)

This pull request implements complete backend support for managing comments on tasks. All APIs follow RESTful CRUD principles, maintain consistency with the existing project structure, and include automated tests.


---

📌 Features Implemented

1. Comment CRUD APIs

API	Method	Description

/tasks/<task_id>/comments	POST	Create a new comment on a task
/comments/<comment_id>	PUT	Update an existing comment
/comments/<comment_id>	DELETE	Delete an existing comment
/tasks/<task_id>/comments	GET (optional)	List all comments for a task



---

📌 Project Structure

backend/
 ├── app/
 │   ├── models/
 │   │   └── comment.py
 │   ├── routes/
 │   │   └── comments.py
 │   └── __init__.py
 ├── tests/
 │   └── test_comments.py
 └── ...


---

📌 Key Decisions

1. Added Comment model aligned with existing architecture.


2. Used blueprint-based routing to maintain clean separation of concerns.


3. Added relational mapping between Task ↔ Comments.


4. Implemented structured error handling for bad requests and missing resources.


5. Added complete test coverage (success + failure cases).




---

📌 Automated Tests

The test suite includes:

Creating a comment

Updating a comment

Deleting a comment

Listing comments

Validation & error handling


Tests use:

pytest

flask.testing client

Database fixtures based on the project template



---

📌 How to Run Locally

Backend Setup

cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask run

Run Tests

pytest


---

📌 Assumptions

Each comment belongs to exactly one task.

Tasks exist before comments can be created.

Comment text is mandatory.

API structure follows consistent REST patterns already used in the codebase.



---

📌 Summary

This PR introduces complete comment management functionality with clean CRUD APIs, comprehensive error handling, and full test coverage, ensuring maintainability and alignment with the template’s architecture.
