from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import jwt, datetime, os

auth_bp = Blueprint("auth", __name__)
SECRET_KEY = os.environ.get("SECRET_KEY", "secret")

def serialize_user(user):
    return {"_id": str(user["_id"]), "email": user["email"]}

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Missing fields"}), 400
    hashed_pw = generate_password_hash(data["password"])
    user = {"email": data["email"], "password": hashed_pw}
    result = request.db.users.insert_one(user)
    user["_id"] = result.inserted_id
    return jsonify(serialize_user(user)), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = request.db.users.find_one({"email": data["email"]})
    if not user or not check_password_hash(user["password"], data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401
    token = jwt.encode(
        {"user_id": str(user["_id"]), "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)},
        SECRET_KEY,
        algorithm="HS256"
    )
    return jsonify({"token": token}), 200
