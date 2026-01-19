from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
CORS(app)

FILE = Path("expenses.json")

# Create file if not exists
if not FILE.exists():
    FILE.write_text("[]")


# ---------- HELPERS ----------

def read_expenses():
    try:
        return json.loads(FILE.read_text())
    except:
        return []


def write_expenses(expenses):
    FILE.write_text(json.dumps(expenses, indent=2))


def sort_by_date_desc(expenses):
    return sorted(
        expenses,
        key=lambda e: datetime.strptime(e["date"], "%Y-%m-%d"),
        reverse=True
    )


# ---------- ROUTES ----------

@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    # GET
    if request.method == "GET":
        expenses = sort_by_date_desc(read_expenses())
        write_expenses(expenses)
        return jsonify(expenses)

    # POST (SAVE)
    if request.method == "POST":
        new_expense = request.json
        expenses = read_expenses()
        expenses.append(new_expense)
        write_expenses(sort_by_date_desc(expenses))
        return jsonify(new_expense), 201


# DELETE BY INDEX (POST → no CORS issues)
@app.route("/expenses/delete/<int:index>", methods=["POST"])
def delete_expense(index):
    expenses = read_expenses()

    if index < 0 or index >= len(expenses):
        return jsonify({"error": "Invalid index"}), 400

    expenses.pop(index)
    write_expenses(expenses)
    return jsonify({"success": True}), 200


# ---------- START ----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

