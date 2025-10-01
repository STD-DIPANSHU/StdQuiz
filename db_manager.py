from pymongo import MongoClient
from bson import ObjectId

class DBManager:
    def __init__(self, mongo_url):
        self.client = MongoClient(mongo_url)
        self.db = self.client["quiz_bot"]
        self.quizzes = self.db["quizzes"]
        self.scores = self.db["scores"]

    def create_quiz(self, user_id, quiz_name):
        quiz = {"owner": user_id, "name": quiz_name}
        result = self.quizzes.insert_one(quiz)
        return str(result.inserted_id)

    def get_user_quizzes(self, user_id):
        return list(self.quizzes.find({"owner": user_id}))

    def save_score(self, quiz_id, user_id, username, score):
        self.scores.insert_one({
            "quiz_id": ObjectId(quiz_id),
            "user_id": user_id,
            "username": username,
            "score": score
        })

    def get_leaderboard(self, quiz_id):
        return list(
            self.scores.find({"quiz_id": ObjectId(quiz_id)})
            .sort("score", -1)
            .limit(10)
        )
