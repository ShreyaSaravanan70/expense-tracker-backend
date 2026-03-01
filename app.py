from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# ---------- LOAD ENV VARIABLES ----------
load_dotenv()
MONGO_URI = os.environ.get("MONGODB_URI")
SECRET_KEY = os.environ.get("SECRET_KEY", "secret")

# ---------- APP SETUP ----------
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ---------- DATABASE SETUP ----------
client = MongoClient(MONGO_URI)
db = client.expense_tracker
users_collection = db.users
expenses_collection = db.expenses

# ---------- HELPERS ----------
def serialize_expense(exp):
    return {
        "_id": str(exp["_id"]),
        "amount": exp["amount"],
        "date": exp["date"],
        "description": exp.get("description", ""),
        "user_id": str(exp.get("user_id"))
    }

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]  # Bearer <token>
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

# ---------- ROUTES ----------
@app.route("/")
def home():
    return jsonify({"message": "Expense Tracker Backend (MongoDB) is running 🚀"}), 200

# ---------- AUTH ----------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Missing fields"}), 400
    if users_collection.find_one({"email": data["email"]}):
        return jsonify({"error": "User already exists"}), 400
    hashed_pw = generate_password_hash(data["password"])
    user = {"email": data["email"], "password": hashed_pw}
    result = users_collection.insert_one(user)
    return jsonify({"_id": str(result.inserted_id), "email": data["email"]}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = users_collection.find_one({"email": data.get("email")})
    if not user or not check_password_hash(user["password"], data.get("password")):
        return jsonify({"error": "Invalid credentials"}), 401
    token = jwt.encode(
        {"user_id": str(user["_id"]), "exp": datetime.utcnow() + timedelta(hours=2)},
        SECRET_KEY,
        algorithm="HS256"
    )
    return jsonify({"token": token}), 200

# ---------- EXPENSES ----------
@app.route("/expenses", methods=["GET", "POST", "OPTIONS"])
@token_required
def expenses():
    if request.method == "OPTIONS":
        return "", 204
    
    if request.method == "GET":
        expenses_list = list(expenses_collection.find({"user_id": request.user_id}))
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
            "description": new_expense.get("description", ""),
            "user_id": request.user_id
        }

        result = expenses_collection.insert_one(expense)
        expense["_id"] = str(result.inserted_id)
        return jsonify(expense), 201

@app.route("/expenses/delete/<expense_id>", methods=["POST", "DELETE", "OPTIONS"])
@token_required
def delete_expense(expense_id):
    if request.method == "OPTIONS":
        return "", 204
    
    result = expenses_collection.delete_one({"_id": ObjectId(expense_id), "user_id": request.user_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Expense not found"}), 404
    return jsonify({"success": True, "deleted_id": expense_id}), 200

# ---------- REPORT ROUTE ----------
@app.route("/expenses/report", methods=["GET"])
@token_required
def report():
    start = request.args.get("from")
    end = request.args.get("to")
    query = {"user_id": request.user_id}
    if start and end:
        query["date"] = {"$gte": start, "$lte": end}
    expenses = list(expenses_collection.find(query))
    return jsonify([serialize_expense(exp) for exp in expenses]), 200

# ---------- START SERVER ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
