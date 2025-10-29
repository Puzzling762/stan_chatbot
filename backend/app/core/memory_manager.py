# app/core/memory_manager.py
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
        Save messages intelligently:
        - Short-term: All messages (for conversation flow)
        - Long-term: Only user's meaningful info (facts, preferences)
        """
        
        self._add_to_buffer(user_id, message, is_user)
        
        
        if is_user and should_save_to_memory(message, is_user):
           
            extracted_facts = self._extract_key_info(message)
            
            
            if isinstance(extracted_facts, list):
                for fact in extracted_facts:
                    if fact:
                        add_memory(
                            user_id=user_id,
                            text=fact,
                            metadata={
                                "turn_id": turn_id,
                                "role": "user",
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                        print(f"💾 Saved to memory: {fact}")
            elif extracted_facts:
                add_memory(
                    user_id=user_id,
                    text=extracted_facts,
                    metadata={
                        "turn_id": turn_id,
                        "role": "user",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                print(f"💾 Saved to memory: {extracted_facts}")
    
    def _extract_key_info(self, message: str):
        """
        Extract MULTIPLE facts from a single message.
        Returns list of facts or single fact string.
        
        Example:
        "My name is Alex and I love anime, especially Attack on Titan"
        → ["Name: Alex", "Loves: anime", "Favorite anime: Attack on Titan"]
        """
        message_lower = message.lower()
        facts = []
        
       
        name_patterns = [
            r"my name is (\w+)",
            r"i'?m (\w+)",
            r"call me (\w+)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match and len(match.group(1)) > 2:
                name = match.group(1).title()
                if name not in ['Okay', 'Good', 'Fine', 'Sad', 'Down', 'Happy']:
                    facts.append(f"Name: {name}")
                    break
        
        
        compound_interest = re.search(r"i love (\w+),?\s*especially (.+?)(?:\.|!|\?|$)", message_lower)
        if compound_interest:
            category = compound_interest.group(1).strip()
            specific = compound_interest.group(2).strip()
            facts.append(f"Loves: {category}")
            facts.append(f"Favorite {category}: {specific}")
        else:
            
            interest_patterns = [
                (r"my fav(?:orite)? (\w+) (?:is|are) (.+?)(?:\.|!|\?|$)", "Favorite {0}: {1}"),
                (r"i love (.+?)(?:\.|!|\?|$)", "Loves: {0}"),
                (r"i like (.+?)(?:\.|!|\?|$)", "Likes: {0}"),
                (r"i'?m (?:really )?into (.+?)(?:\.|!|\?|$)", "Into: {0}"),
                (r"i'?m a (?:big |huge )?fan of (.+?)(?:\.|!|\?|$)", "Fan of: {0}"),
                (r"i hate (.+?)(?:\.|!|\?|$)", "Dislikes: {0}"),
                (r"i can'?t stand (.+?)(?:\.|!|\?|$)", "Dislikes: {0}"),
            ]
            
            for pattern, template in interest_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    if "{0}" in template and "{1}" in template:
                        facts.append(template.format(match.group(1).title(), match.group(2).strip().title()))
                    else:
                        captured = match.group(1).strip()
                        captured = re.sub(r'\s+', ' ', captured)
                        facts.append(template.format(captured))
                    break
        
       
        background_patterns = [
            (r"i'?m studying (.+?)(?:\.|!|\?|at |in |$)", "Studies: {0}"),
            (r"i study (.+?)(?:\.|!|\?|at |in |$)", "Studies: {0}"),
            (r"my major is (.+?)(?:\.|!|\?|$)", "Major: {0}"),
            (r"i'?m (?:a |an )?(.+?) major", "Major: {0}"),
            (r"i work (?:as |at )?(.+?)(?:\.|!|\?|$)", "Works: {0}"),
            (r"i live in (.+?)(?:\.|!|\?|$)", "Lives in: {0}"),
            (r"i'?m from (.+?)(?:\.|!|\?|$)", "From: {0}"),
            (r"i go to (.+?)(?:university|college|school)", "Attends: {0}"),
        ]
        
        for pattern, template in background_patterns:
            match = re.search(pattern, message_lower)
            if match:
                captured = match.group(1).strip().title()
                captured = re.sub(r'^(The |A |An )', '', captured)
                facts.append(template.format(captured))
                break
        
       
        activity_patterns = [
            (r"i play (.+?)(?:\.|!|\?|$)", "Plays: {0}"),
            (r"i watch (.+?)(?:\.|!|\?|$)", "Watches: {0}"),
            (r"i listen to (.+?)(?:\.|!|\?|$)", "Listens to: {0}"),
        ]
        
        for pattern, template in activity_patterns:
            match = re.search(pattern, message_lower)
            if match:
                facts.append(template.format(match.group(1).strip()))
                break
        
        
        if len(facts) > 1:
            return facts 
        elif len(facts) == 1:
            return facts[0]  
        elif len(message.split()) >= 6 and any(word in message_lower for word in ['i', 'my', 'me']):
            return message 
        
        return ""
    
    def _add_to_buffer(self, user_id: str, message: str, is_user: bool):
        """Maintain rolling window of recent conversation."""
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
    
    def recall_context(self, user_id: str, query: str, top_k: int = 5) -> str:
        """
        Retrieve most relevant long-term memories.
        Increased top_k to catch more related memories.
        """
        memories = retrieve_memories(user_id, query, top_k)
        
        if not memories or len(memories) == 0:
            return ""
        
        formatted = []
        seen = set()  
        
        for mem in memories[:top_k]:
            clean = mem.strip()

            if len(clean) > 8 and clean not in seen:
                formatted.append(f"- {clean}")
                seen.add(clean)
        
        if not formatted:
            return ""
        
        return "\n".join(formatted)
    
    def clear_session(self, user_id: str):
        """Clear short-term buffer (for new sessions)."""
        if user_id in self.short_term_buffer:
            self.short_term_buffer[user_id] = []