import json, os
from collections import defaultdict

class DataManager:
    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump({}, f)
        with open(path, "r") as f:
            self.data = json.load(f)

    def add_message(self, user_id, msg):
        user_id = str(user_id)
        self.data.setdefault(user_id, {"messages": []})
        self.data[user_id]["messages"].append(msg)
        if len(self.data[user_id]["messages"]) > 200:
            self.data[user_id]["messages"] = self.data[user_id]["messages"][-200:]
        self._save()

    def get_user_data(self, user_id):
        return self.data.get(str(user_id), {"messages": []})

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)
