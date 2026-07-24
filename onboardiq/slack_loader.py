import json
import re
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document

class SlackDirectoryLoader:
    """Custom Loader to ingest Slack JSON exports and group messages into threaded conversations."""

    def __init__(self, slack_dir_path: Path):
        self.slack_dir_path = Path(slack_dir_path)
        self.users = self._load_users()

    def _load_users(self) -> Dict[str, Dict[str, str]]:
        """Loads user ID mapping from users.json."""
        users_file = self.slack_dir_path / "users.json"
        if users_file.exists():
            with open(users_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _get_user_display_name(self, user_id: str) -> str:
        """Returns the real name of a user or their ID if not found."""
        if user_id in self.users:
            user_info = self.users[user_id]
            return f"{user_info.get('real_name')} ({user_info.get('title', 'Staff')})"
        return user_id

    def _replace_user_mentions(self, text: str) -> str:
        """Replaces Slack style mentions <@U12345> with user real names."""
        def replace(match):
            user_id = match.group(1)
            return f"@{self._get_user_display_name(user_id)}"
        
        return re.sub(r"<@(U[A-Z0-9]+)>", replace, text)

    def load(self) -> List[Document]:
        """Loads and parses all channel JSON files in the Slack directory."""
        documents = []
        
        # Iterate over all JSON files except users.json
        for file_path in self.slack_dir_path.glob("*.json"):
            if file_path.name == "users.json":
                continue
                
            channel_name = file_path.stem
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    messages = json.load(f)
            except Exception as e:
                print(f"Error loading Slack log {file_path}: {e}")
                continue

            # Group messages into threads
            threads: Dict[str, Dict[str, Any]] = {}
            standalone_messages: List[Dict[str, Any]] = []

            for msg in messages:
                if msg.get("type") != "message":
                    continue

                ts = msg.get("ts")
                thread_ts = msg.get("thread_ts")
                
                # Check if it is part of a thread
                if thread_ts:
                    if thread_ts not in threads:
                        threads[thread_ts] = {
                            "parent": None,
                            "replies": []
                        }
                    
                    if ts == thread_ts:
                        threads[thread_ts]["parent"] = msg
                    else:
                        threads[thread_ts]["replies"].append(msg)
                else:
                    # Message with no thread
                    standalone_messages.append(msg)

            # Process threads
            for thread_id, thread_data in threads.items():
                parent = thread_data["parent"]
                replies = thread_data["replies"]
                
                # If we missed the parent message in this export log chunk, use the first reply as placeholder
                if not parent and replies:
                    parent = replies[0]
                    replies = replies[1:]
                
                if not parent:
                    continue

                # Format thread text
                parent_author = self._get_user_display_name(parent.get("user", ""))
                parent_text = self._replace_user_mentions(parent.get("text", ""))
                
                formatted_text = f"Slack Channel: #{channel_name}\n"
                formatted_text += f"Conversation Thread ID: {thread_id}\n"
                formatted_text += f"[{parent_author}]: {parent_text}\n"
                
                # Sort replies by timestamp
                replies.sort(key=lambda x: float(x.get("ts", 0)))
                for reply in replies:
                    reply_author = self._get_user_display_name(reply.get("user", ""))
                    reply_text = self._replace_user_mentions(reply.get("text", ""))
                    formatted_text += f"  - Reply from [{reply_author}]: {reply_text}\n"

                # Create document
                metadata = {
                    "source": str(file_path.relative_to(self.slack_dir_path.parent.parent)),
                    "type": "slack",
                    "channel": channel_name,
                    "thread_id": thread_id,
                    "timestamp": parent.get("ts"),
                    "author": parent_author
                }
                documents.append(Document(page_content=formatted_text, metadata=metadata))

            # Process standalone messages
            for msg in standalone_messages:
                author = self._get_user_display_name(msg.get("user", ""))
                text = self._replace_user_mentions(msg.get("text", ""))
                
                formatted_text = f"Slack Channel: #{channel_name}\n"
                formatted_text += f"[{author}]: {text}\n"

                metadata = {
                    "source": str(file_path.relative_to(self.slack_dir_path.parent.parent)),
                    "type": "slack",
                    "channel": channel_name,
                    "timestamp": msg.get("ts"),
                    "author": author
                }
                documents.append(Document(page_content=formatted_text, metadata=metadata))

        return documents
