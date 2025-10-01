from pymongo import MongoClient
from bson.objectid import ObjectId

MONGO_URL = "mongodb://localhost:27017"  # ya MongoDB Atlas ka URL
client = MongoClient(MONGO_URL)
db = client["quizbot"]
quizzes_col = db["quizzes"]

def create_quiz(user_id, title, description=""):
    quiz = {
        "user_id": user_id,
        "title": title,
        "description": description,
        "questions": []
    }
    result = quizzes_col.insert_one(quiz)
    return str(result.inserted_id)

def add_question(quiz_id, question, options, correct_index):
    quizzes_col.update_one(
        {"_id": ObjectId(quiz_id)},
        {"$push": {
            "questions": {
                "question": question,
                "options": options,
                "correct_index": correct_index
            }
        }}
    )

def get_quiz(quiz_id):
    return quizzes_col.find_one({"_id": ObjectId(quiz_id)})

def get_user_quizzes(user_id):
    return list(quizzes_col.find({"user_id": user_id}))
