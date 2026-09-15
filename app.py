from flask import Flask, request, jsonify, render_template
import sqlite3
import os
import re

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "students.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            department TEXT NOT NULL,
            year INTEGER NOT NULL,
            cgpa REAL
        )
    """)
    conn.commit()
    conn.close()


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_student(data, partial=False):
    errors = {}

    def required(field, label):
        if not partial and not str(data.get(field, "")).strip():
            errors[field] = f"{label} is required."

    required("name", "Name")
    required("roll_no", "Roll number")
    required("email", "Email")
    required("department", "Department")

    if "email" in data and data.get("email"):
        if not EMAIL_RE.match(str(data["email"]).strip()):
            errors["email"] = "Enter a valid email address."

    if "year" in data and data.get("year") not in (None, ""):
        try:
            y = int(data["year"])
            if y < 1 or y > 5:
                errors["year"] = "Year must be between 1 and 5."
        except (ValueError, TypeError):
            errors["year"] = "Year must be a number."
    elif not partial:
        errors["year"] = "Year is required."

    if "cgpa" in data and data.get("cgpa") not in (None, ""):
        try:
            c = float(data["cgpa"])
            if c < 0 or c > 10:
                errors["cgpa"] = "CGPA must be between 0 and 10."
        except (ValueError, TypeError):
            errors["cgpa"] = "CGPA must be a number."

    return errors


@app.route("/")
def index():
    return render_template("index.html")


# ---------- REST API ----------

@app.route("/api/students", methods=["GET"])
def get_students():
    search = request.args.get("search", "").strip()
    conn = get_db()
    if search:
        like = f"%{search}%"
        rows = conn.execute(
            "SELECT * FROM students WHERE name LIKE ? OR roll_no LIKE ? OR department LIKE ? ORDER BY id DESC",
            (like, like, like),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(dict(row))


@app.route("/api/students", methods=["POST"])
def create_student():
    data = request.get_json(silent=True) or {}
    errors = validate_student(data)
    if errors:
        return jsonify({"errors": errors}), 400

    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO students (name, roll_no, email, department, year, cgpa) VALUES (?, ?, ?, ?, ?, ?)",
            (
                data["name"].strip(),
                data["roll_no"].strip(),
                data["email"].strip(),
                data["department"].strip(),
                int(data["year"]),
                float(data["cgpa"]) if data.get("cgpa") not in (None, "") else None,
            ),
        )
        conn.commit()
        new_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"errors": {"roll_no": "Roll number already exists."}}), 400
    conn.close()
    return jsonify({"message": "Student created", "id": new_id}), 201


@app.route("/api/students/<int:student_id>", methods=["PUT", "PATCH"])
def update_student(student_id):
    data = request.get_json(silent=True) or {}
    partial = request.method == "PATCH"
    errors = validate_student(data, partial=partial)
    if errors:
        return jsonify({"errors": errors}), 400

    conn = get_db()
    existing = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Student not found"}), 404

    merged = dict(existing)
    merged.update({k: v for k, v in data.items() if v is not None})

    try:
        conn.execute(
            "UPDATE students SET name=?, roll_no=?, email=?, department=?, year=?, cgpa=? WHERE id=?",
            (
                str(merged["name"]).strip(),
                str(merged["roll_no"]).strip(),
                str(merged["email"]).strip(),
                str(merged["department"]).strip(),
                int(merged["year"]),
                float(merged["cgpa"]) if merged.get("cgpa") not in (None, "") else None,
                student_id,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"errors": {"roll_no": "Roll number already exists."}}), 400
    conn.close()
    return jsonify({"message": "Student updated"})


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Student not found"}), 404
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Student deleted"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
