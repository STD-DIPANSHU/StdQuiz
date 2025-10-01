from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URL)
db = client["quizbot"]

# Quiz collection
quiz_col = db["quizzes"]
# Scores collection
score_col = db["scores"]

def save_quiz(owner_id, title, questions):
    quiz = {"owner_id": owner_id, "title": title, "questions": questions}
    result = quiz_col.insert_one(quiz)
    return result.inserted_id

def get_quiz(quiz_id):
    return quiz_col.find_one({"_id": quiz_id})

def save_score(user_id, group_id, quiz_id, correct):
    score_col.update_one(
        {"user_id": user_id, "group_id": group_id, "quiz_id": quiz_id},
        {"$inc": {"correct": correct}},
        upsert=True
    )

def get_leaderboard(group_id, quiz_id):
    return list(score_col.find({"group_id": group_id, "quiz_id": quiz_id}))
