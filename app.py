from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
from datetime import datetime

# ---------- LOAD ENV VARIABLES ----------
load_dotenv()
MONGO_URI = os.environ.get("MONGODB_URI")  # e.g., mongodb+srv://user:pass@cluster.mongodb.net/dbname

# ---------- APP SETUP ----------
app = Flask(__name__)
CORS(app)

# ---------- DATABASE SETUP ----------
client = MongoClient(MONGO_URI)
db = client.expense_tracker  # database
collection = db.expenses      # collection

# ---------- HELPERS ----------
def serialize_expense(exp):
    return {
        "_id": str(exp["_id"]),
        "amount": exp["amount"],
        "date": exp["date"],
        "description": exp.get("description", "")
    }

# ---------- ROUTES ----------
@app.route("/")
def home():
    return jsonify({"message": "Expense Tracker Backend (MongoDB) is running 🚀"}), 200

@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    if request.method == "GET":
        expenses_list = list(collection.find())
        # Sort newest first
        expenses_list.sort(
            key=lambda e: datetime.strptime(e["date"], "%Y-%m-%d"),
            reverse=True
        )
        return jsonify([serialize_expense(exp) for exp in expenses_list]), 200

    if request.method == "POST":
        new_expense = request.get_json()
        if not new_expense or "amount" not in new_expense or "date" not in new_expense:
            return jsonify({"error": "Invalid expense data"}), 400

        expense = {
            "amount": new_expense["amount"],
            "date": new_expense["date"],
            "description": new_expense.get("description", "")
        }

        result = collection.insert_one(expense)
        expense["_id"] = str(result.inserted_id)
        return jsonify(expense), 201

@app.route("/expenses/delete/<expense_id>", methods=["POST", "DELETE"])
def delete_expense(expense_id):
    result = collection.delete_one({"_id": ObjectId(expense_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Expense not found"}), 404
    return jsonify({"success": True, "deleted_id": expense_id}), 200

@app.route("/force-insert")
def force_insert():
    doc = {
        "amount": 123,
        "date": "2026-01-21",
        "description": "FORCE_TEST"
    }
    result = collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return jsonify({"inserted_id": doc["_id"]}), 201

# ---------- START SERVER ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
