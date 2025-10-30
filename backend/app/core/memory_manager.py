from app.db.vector_store import add_memory, retrieve_memories
from app.core.prompt_templates import should_save_to_memory
from datetime import datetime
import re

class MemoryManager:
    def __init__(self):
        self.short_term_buffer = {}  
        self.max_buffer_size = 8  
    
    def save_interaction(self, user_id: str, message: str, turn_id: int, is_user: bool = True):
        """
        Intelligently save messages.
        Short-term: Everything (for flow)
        Long-term: Only meaningful content
        """
        self._add_to_buffer(user_id, message, is_user)
        
        if should_save_to_memory(message, is_user):
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
    # every second message made by limit getting reached so started saving messages which where given by user only
    def _extract_key_info(self, message: str, is_user: bool) -> str:
        """
        Extract only the KEY information from a message.
        """
        if not is_user:
            return ""
        
        message_lower = message.lower().strip()
        
        name_patterns = [
            r"my name is (\w+)",
            r"i'?m (\w+)",
            r"call me (\w+)",
            r"i am (\w+)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match and len(match.group(1)) > 2:  
                name = match.group(1).title()
                if name not in ['Into', 'From', 'Love', 'Like']:  
                    return f"User's name: {name}"
        
        anime_patterns = [
            (r"i love (?:watching |the anime )?([^,.!?]+?)(?:\s+anime|\s+show)?(?:\.|,|$)", "Loves anime: {0}"),
            (r"i like (?:watching |the anime )?([^,.!?]+?)(?:\s+anime|\s+show)?(?:\.|,|$)", "Likes anime: {0}"),
            (r"i'?m (?:really )?into (?:the anime )?([^,.!?]+?)(?:\s+anime)?(?:\.|,|$)", "Into anime: {0}"),
            (r"my fav(?:orite)? anime is ([^,.!?]+)", "Favorite anime: {0}"),
        ]
        
        for pattern, template in anime_patterns:
            match = re.search(pattern, message_lower)
            if match:
                content = match.group(1).strip()
                
                if len(content) > 2 and content not in ['it', 'that', 'this', 'anime']:
                    return template.format(content.title())
        
        sports_patterns = [
            (r"my fav(?:orite)? (?:football |soccer )?(?:team|club) is ([^,.!?]+)", "Favorite club: {0}"),
            (r"i support ([^,.!?]+?)(?:\s+(?:fc|football club))?(?:\.|,|$)", "Supports: {0}"),
            (r"i'?m a(?: big)? ([^,.!?]+?) fan", "Fan of: {0}"),
        ]
        
        for pattern, template in sports_patterns:
            match = re.search(pattern, message_lower)
            if match:
                content = match.group(1).strip()
                if len(content) > 2:
                    return template.format(content.title())
        
        
        general_patterns = [
            (r"my fav(?:orite)? (\w+) is ([^,.!?]+)", "Favorite {0}: {1}"),
            (r"i love ([^,.!?]+?)(?:\.|,|$)", "Loves: {0}"),
            (r"i like ([^,.!?]+?)(?:\.|,|$)", "Likes: {0}"),
            (r"i hate ([^,.!?]+?)(?:\.|,|$)", "Dislikes: {0}"),
        ]
        
        for pattern, template in general_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if "{0}" in template and "{1}" in template:
                    return template.format(match.group(1).strip(), match.group(2).strip().title())
                else:
                    content = match.group(1).strip()
                    if len(content) > 2:
                        return template.format(content.title())
        
        info_patterns = [
            (r"i (?:study|am studying) ([^,.!?]+)", "Studies: {0}"),
            (r"i (?:work|am working) (?:as |at )?([^,.!?]+)", "Works: {0}"),
            (r"i live in ([^,.!?]+)", "Lives in: {0}"),
            (r"i'?m from ([^,.!?]+)", "From: {0}"),
        ]
        
        for pattern, template in info_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return template.format(match.group(1).strip().title())
        
        if len(message.split()) >= 5:
            return message
        
        return ""
    
    def _add_to_buffer(self, user_id: str, message: str, is_user: bool):
        """Maintain rolling buffer of recent messages."""
        if user_id not in self.short_term_buffer:
            self.short_term_buffer[user_id] = []
        
        prefix = "User" if is_user else "STAN"
        self.short_term_buffer[user_id].append(f"{prefix}: {message}")
        
        if len(self.short_term_buffer[user_id]) > self.max_buffer_size:
            self.short_term_buffer[user_id].pop(0)
    
    def get_recent_context(self, user_id: str) -> str:
        """Get recent conversation for immediate context."""
        if user_id not in self.short_term_buffer or not self.short_term_buffer[user_id]:
            return ""
        
        recent = self.short_term_buffer[user_id][-6:]
        return "\n".join(recent)
    
    def recall_context(self, user_id: str, query: str, top_k: int = 4) -> str:
        """
        Retrieve the most relevant memories.
        Returns clean, factual information.
        """
        memories = retrieve_memories(user_id, query, top_k)
        
        if not memories or len(memories) == 0:
            return ""
        
        formatted = []
        seen = set()  
        
        for mem in memories[:top_k]:
            clean = mem.strip()
            if len(clean) > 10 and clean not in seen:
                formatted.append(f"- {clean}")
                seen.add(clean)
        
        return "\n".join(formatted) if formatted else ""
    
    def clear_session(self, user_id: str):
        """Clear short-term buffer."""
        if user_id in self.short_term_buffer:
            self.short_term_buffer[user_id] = []