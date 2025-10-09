import json
import os
from collections import defaultdict
from datetime import datetime

class DataManager:
    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump({}, f)
        with open(path, "r") as f:
            self.data = json.load(f)

    def add_message(self, user_id, msg, skip_save=False):
        """
        Add a message to user's history with timestamp
        
        Args:
            user_id: User's Discord ID
            msg: Message content
            skip_save: If True, don't save immediately (useful for bulk operations)
        """
        user_id = str(user_id)
        
        # Initialize user data structure if needed
        if user_id not in self.data:
            self.data[user_id] = {
                "messages": [],
                "first_seen": datetime.now().isoformat(),
                "total_messages": 0
            }
        
        # Add message
        self.data[user_id]["messages"].append(msg)
        self.data[user_id]["total_messages"] = self.data[user_id].get("total_messages", 0) + 1
        self.data[user_id]["last_seen"] = datetime.now().isoformat()
        
        # Keep only last 500 messages for deep history (increased from 200)
        if len(self.data[user_id]["messages"]) > 500:
            self.data[user_id]["messages"] = self.data[user_id]["messages"][-500:]
        
        if not skip_save:
            self._save()

    def get_user_data(self, user_id):
        """
        Get all data for a user
        """
        return self.data.get(str(user_id), {"messages": [], "total_messages": 0})

    def get_all_users(self):
        """
        Get list of all user IDs with message counts
        """
        return {
            user_id: len(data.get("messages", []))
            for user_id, data in self.data.items()
        }

    def get_total_messages(self):
        """
        Get total message count across all users
        """
        return sum(len(data.get("messages", [])) for data in self.data.values())

    def clear_user_history(self, user_id):
        """
        Clear a user's message history (for privacy/GDPR)
        """
        user_id = str(user_id)
        if user_id in self.data:
            self.data[user_id]["messages"] = []
            self._save()
            return True
        return False

    def _save(self):
        """
        Save data to file with pretty printing
        """
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)