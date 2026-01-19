from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime

# ---------- APP SETUP ----------
app = Flask(__name__)
CORS(app)

FILE = Path("expenses.json")

# Ensure the expenses file exists
if not FILE.exists():
    FILE.write_text("[]")


# ---------- HELPERS ----------

def read_expenses():
    """Read expenses from the JSON file."""
    try:
        return json.loads(FILE.read_text())
    except json.JSONDecodeError:
        return []


def write_expenses(expenses):
    """Write expenses to the JSON file with indentation."""
    FILE.write_text(json.dumps(expenses, indent=2))


def sort_by_date_desc(expenses):
    """Sort expenses by date in descending order."""
    return sorted(
        expenses,
        key=lambda e: datetime.strptime(e["date"], "%Y-%m-%d"),
        reverse=True
    )


# ---------- ROUTES ----------

@app.route("/")
def home():
    """Root route for health check."""
    return jsonify({"message": "Expense Tracker Backend is running 🚀"}), 200


@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    if request.method == "GET":
        expenses_list = sort_by_date_desc(read_expenses())
        write_expenses(expenses_list)
        return jsonify(expenses_list), 200

    elif request.method == "POST":
        new_expense = request.get_json()
        if not new_expense or "amount" not in new_expense or "date" not in new_expense:
            return jsonify({"error": "Invalid expense data"}), 400

        expenses_list = read_expenses()
        expenses_list.append(new_expense)
        write_expenses(sort_by_date_desc(expenses_list))
        return jsonify(new_expense), 201


@app.route("/expenses/delete/<int:index>", methods=["POST"])
def delete_expense(index):
    expenses_list = read_expenses()

    if index < 0 or index >= len(expenses_list):
        return jsonify({"error": "Invalid index"}), 400

    deleted = expenses_list.pop(index)
    write_expenses(expenses_list)
    return jsonify({"success": True, "deleted": deleted}), 200


# ---------- START ----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
