# app/core/memory_manager.py
from app.db.vector_store import add_memory, retrieve_memories
from app.core.prompt_templates import should_save_to_memory
from datetime import datetime
import re

class MemoryManager:
    def __init__(self):
        self.short_term_buffer = {}  # user_id -> list of recent messages
        self.max_buffer_size = 6  # Keep only last 6 messages for immediate context
    
    def save_interaction(self, user_id: str, message: str, turn_id: int, is_user: bool = True):
        """
        Intelligently save messages.
        Short-term: Everything (for flow)
        Long-term: Only meaningful content
        """
        # Always save to short-term buffer
        self._add_to_buffer(user_id, message, is_user)
        
        # Only save important stuff to long-term memory
        if should_save_to_memory(message, is_user):
            # Extract key information
            clean_message = self._extract_key_info(message, is_user)
            
            if clean_message:
                role = "user" if is_user else "assistant"
                add_memory(
                    user_id=user_id,
                    text=clean_message,
                    metadata={
                        "turn_id": turn_id,
                        "role": role,
                        "timestamp": datetime.now().isoformat()
                    }
                )
    
    def _extract_key_info(self, message: str, is_user: bool) -> str:
        """
        Extract only the KEY information from a message.
        Examples:
        - "My name is Alex" â†’ "User's name is Alex"
        - "I love Attack on Titan" â†’ "Loves anime: Attack on Titan"
        - "My favorite player is Ronaldo" â†’ "Favorite football player: Ronaldo"
        """
        if not is_user:
            # Don't save STAN's responses to long-term memory
            # (reduces clutter and "you mentioned" references)
            return ""
        
        message_lower = message.lower()
        
        # Pattern 1: Names
        name_match = re.search(r"my name is (\w+)", message_lower)
        if name_match:
            return f"User's name: {name_match.group(1).title()}"
        
        # Pattern 2: Favorites
        fav_patterns = [
            (r"my fav(?:orite)? (\w+) is (.+?)(?:\.|$)", "Favorite {0}: {1}"),
            (r"i love (.+?)(?:\.|$)", "Loves: {0}"),
            (r"i like (.+?)(?:\.|$)", "Likes: {0}"),
            (r"i'm a (?:big )?fan of (.+?)(?:\.|$)", "Fan of: {0}"),
            (r"i hate (.+?)(?:\.|$)", "Dislikes: {0}"),
        ]
        
        for pattern, template in fav_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if "{0}" in template and "{1}" in template:
                    return template.format(match.group(1).title(), match.group(2).strip())
                else:
                    return template.format(match.group(1).strip())
        
        # Pattern 3: Personal info
        info_patterns = [
            (r"i (?:study|am studying) (.+)", "Studies: {0}"),
            (r"i (?:work|am working) (?:as |at )?(.+)", "Works: {0}"),
            (r"i live in (.+)", "Lives in: {0}"),
            (r"i'm from (.+)", "From: {0}"),
        ]
        
        for pattern, template in info_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return template.format(match.group(1).strip())
        
        # If no pattern matched but it's a substantial message, save as-is
        if len(message.split()) >= 5:
            return message
        
        return ""
    
    def _add_to_buffer(self, user_id: str, message: str, is_user: bool):
        """Maintain rolling buffer of recent messages."""
        if user_id not in self.short_term_buffer:
            self.short_term_buffer[user_id] = []
        
        prefix = "User" if is_user else "STAN"
        self.short_term_buffer[user_id].append(f"{prefix}: {message}")
        
        # Keep only last N messages
        if len(self.short_term_buffer[user_id]) > self.max_buffer_size:
            self.short_term_buffer[user_id].pop(0)
    
    def get_recent_context(self, user_id: str) -> str:
        """Get recent conversation for immediate context."""
        if user_id not in self.short_term_buffer or not self.short_term_buffer[user_id]:
            return ""
        
        # Return last 4 messages (2 exchanges)
        recent = self.short_term_buffer[user_id][-4:]
        return "\n".join(recent)
    
    def recall_context(self, user_id: str, query: str, top_k: int = 2) -> str:
        """
        Retrieve ONLY the most relevant memories.
        Returns clean, factual information without context markers.
        """
        memories = retrieve_memories(user_id, query, top_k)
        
        if not memories or len(memories) == 0:
            return ""
        
        # Format memories as clean facts
        formatted = []
        for mem in memories[:top_k]:
            # Clean up the memory text
            clean = mem.strip()
            if len(clean) > 10:  # Only include substantial memories
                formatted.append(f"- {clean}")
        
        return "\n".join(formatted) if formatted else ""
    
    def clear_session(self, user_id: str):
        """Clear short-term buffer."""
        if user_id in self.short_term_buffer:
            self.short_term_buffer[user_id] = []