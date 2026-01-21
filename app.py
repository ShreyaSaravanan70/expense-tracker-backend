from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables (only needed locally)
load_dotenv()

# ---------- MONGODB SETUP ----------
MONGO_URI = os.environ.get("MONGODB_URI")
client = MongoClient(MONGO_URI)
db = client.expense_tracker
collection = db.expenses

# ---------- APP SETUP ----------
app = Flask(__name__)
CORS(app)

# ---------- HELPERS ----------

def serialize_expense(expense):
    """Convert MongoDB document to JSON-friendly format."""
    return {
        "_id": str(expense["_id"]),
        "amount": expense.get("amount"),
        "date": expense.get("date"),
        "category": expense.get("category", ""),
        "description": expense.get("description", "")
    }

# ---------- ROUTES ----------

@app.route("/")
def home():
    """Root route for health check."""
    return jsonify({"message": "Expense Tracker Backend is running 🚀"}), 200

@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    if request.method == "GET":
        # Fetch all expenses, sorted by date descending
        expenses_list = list(collection.find())
        expenses_list.sort(
            key=lambda e: datetime.strptime(e["date"], "%Y-%m-%d"),
            reverse=True
        )
        return jsonify([serialize_expense(e) for e in expenses_list]), 200

    elif request.method == "POST":
        new_expense = request.get_json()
        if not new_expense or "amount" not in new_expense or "date" not in new_expense:
            return jsonify({"error": "Invalid expense data"}), 400

        result = collection.insert_one(new_expense)
        new_expense["_id"] = str(result.inserted_id)
        return jsonify(new_expense), 201

@app.route("/expenses/delete/<expense_id>", methods=["POST"])
def delete_expense(expense_id):
    try:
        result = collection.delete_one({"_id": ObjectId(expense_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Expense not found"}), 404
        return jsonify({"success": True, "deleted_id": expense_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------- START SERVER ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
