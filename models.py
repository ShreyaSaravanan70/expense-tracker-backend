from bson.objectid import ObjectId

# ---------- EXPENSE MODEL ----------
class Expense:
    def __init__(self, amount, date, description="", _id=None):
        self.amount = amount
        self.date = date
        self.description = description
        self._id = str(_id) if _id else None

    def serialize(self):
        return {
            "_id": self._id,
            "amount": self.amount,
            "date": self.date,
            "description": self.description
        }

    @staticmethod
    def from_dict(data):
        return Expense(
            amount=data.get("amount"),
            date=data.get("date"),
            description=data.get("description", ""),
            _id=data.get("_id")
        )


# ---------- USER MODEL ----------
class User:
    def __init__(self, email, password, name="", _id=None):
        self.email = email
        self.password = password  # hashed password
        self.name = name
        self._id = str(_id) if _id else None

    def serialize(self):
        return {
            "_id": self._id,
            "email": self.email,
            "name": self.name
        }

    @staticmethod
    def from_dict(data):
        return User(
            email=data.get("email"),
            password=data.get("password"),
            name=data.get("name", ""),
            _id=data.get("_id")
        )
