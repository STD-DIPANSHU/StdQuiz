from pymongo import MongoClient
from config import MONGO_URL

client = MongoClient(MONGO_URL)
db = client["quizbot"]

quizzes_collection = db["quizzes"]
responses_collection = db["responses"]


def save_quiz(user_id, question, options, correct_answer):
    quiz = {
        "user_id": user_id,
        "question": question,
        "options": options,
        "correct_answer": correct_answer
    }
    quizzes_collection.insert_one(quiz)


def get_all_quizzes():
    return list(quizzes_collection.find())


def save_response(user_id, question, selected_option, is_correct):
    response = {
        "user_id": user_id,
        "question": question,
        "selected_option": selected_option,
        "is_correct": is_correct
    }
    responses_collection.insert_one(response)


def get_leaderboard():
    pipeline = [
        {"$match": {"is_correct": True}},
        {"$group": {"_id": "$user_id", "score": {"$sum": 1}}},
        {"$sort": {"score": -1}}
    ]
    return list(responses_collection.aggregate(pipeline))
