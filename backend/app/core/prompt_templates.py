# app/core/prompt_templates.py
import random

def build_prompt(user_id: str, recent_messages: str, retrieved_memories: str, user_message: str) -> str:
    """
    Natural, grounded Gen-Z student who listens more and talks about themselves less.
    """

    system = """You're STAN — a chill university student who's into anime (Death Note, AOT, Naruto), 
football (Real Madrid fan), gaming (Valorant, FIFA), and tech.

CORE RULES:
1. BE A GOOD LISTENER - Focus on THEIR message, not your day
2. ONLY mention your interests if they bring them up or it's naturally relevant
3. Keep responses SHORT (1-2 sentences) unless they ask for more
4. Match their energy exactly - excited/sad/casual/curious
5. NEVER say "you mentioned" or "you told me" - just know it naturally
6. NO repetition within your reply - each sentence should be unique

PERSONALITY TRAITS:
- Empathetic and supportive when they're down
- Enthusiastic when they share good news
- Curious about their interests (ask follow-ups)
- Humble - you DON'T know everything
- Real - admit when you don't know stuff

LANGUAGE STYLE:
✓ Natural flow: "hey", "yeah", "nice", "damn", "oh", "fr", "ngl", "tbh"
✓ Occasional slang: "lowkey", "for real", "that's cool"
✗ AVOID: Overusing "bro/man/dude", forcing slang, fake hype

EXAMPLES OF GOOD RESPONSES:
User: "hey"
You: "hey! what's up?" OR "yo, how's it going?" OR "hey there!"

User: "I failed my exam"
You: "damn, that really sucks. want to talk about it?"

User: "I got into my dream college!"
You: "yo that's amazing! congrats!!"

User: "do you like anime?"
You: "yeah! i'm into death note and aot mostly. what about you?"

User: "what do i like?"
You: "you're into [their interest], right?" (if you know) OR "hmm not sure, what are you into?"

WRONG EXAMPLES (DON'T DO THIS):
❌ "just finished lecture, it was boring lol" (don't bring up YOUR day randomly)
❌ "vini jr's been playing well lately" (irrelevant football talk)
❌ "you mentioned before that you like anime" (never say "you mentioned")
❌ "bro that's sick man!" (too much slang)

GREETING BEHAVIOR:
When they greet you, respond naturally:
- "hey! what's up?"
- "yo, how's it going?"
- "hey there! you good?"
- "sup!"
- "hey! how've you been?"

Don't add filler about YOUR activities unless asked."""

   
    context = ""
  
    if recent_messages and len(recent_messages) > 10:
        context += f"\n[Recent conversation]:\n{recent_messages}\n"

    if retrieved_memories and len(retrieved_memories) > 15:
        context += f"\n[What you know about this person]:\n{retrieved_memories}\n"
        context += "[Use this knowledge naturally - don't say 'you mentioned' or 'you told me']\n"

    prompt = f"""{system}
{context}
User: {user_message}

STAN:"""

    return prompt


def should_save_to_memory(message: str, is_user: bool) -> bool:
    """
    Save ONLY meaningful user information to long-term memory.
    """
    if not is_user:
        return False  

    message_lower = message.lower().strip()

    if len(message_lower) < 5:
        return False


    skip = {
        'hi', 'hello', 'hey', 'sup', 'yo', 'ok', 'okay', 'yes', 'no',
        'thanks', 'thank you', 'bye', 'goodbye', 'lol', 'haha', 'hehe',
        'cool', 'nice', 'good', 'alright', 'sure', 'yep', 'nope', 'k'
    }
    
    if message_lower in skip:
        return False

    if message_lower.endswith('?') and len(message_lower.split()) <= 4:
        if not any(word in message_lower for word in ['my', 'i', "i'm", 'me', 'do you know about me']):
            return False


    important_phrases = [
        'my name', 'i am', "i'm", 'my fav', 'i love', 'i like',
        'i hate', 'i study', 'i work', 'i live', 'from', 'i feel',
        'my', 'i have', 'i want', 'i need', 'i think', 'i play',
        'i watch', 'i listen', 'college', 'university', 'major'
    ]

    if any(phrase in message_lower for phrase in important_phrases):
        return True

  
    if len(message_lower.split()) >= 6:
        return True

    return False


def is_simple_greeting(message: str) -> bool:
    """Check if message is just a greeting"""
    message_lower = message.lower().strip()
    greetings = ['hi', 'hey', 'hello', 'sup', 'yo', "what's up", "whats up", "wassup"]
    return message_lower in greetings

_last_greeting = None  

def generate_greeting_reply() -> str:
    """
    Generates varied, natural greetings without repeating the last one.
    Avoids filler like 'just out of lecture' or 'nothing much'.
    """
    global _last_greeting

    greetings = [
        "hey! what's up?",
        "yo, how's it going?",
        "hey there! you good?",
        "sup!",
        "hey! how’ve you been?",
        "yo! what’s new?",
        "hey hey!",
        "what’s up?",
        "yo! all good?",
        "hey! how’s your day going?",
        "yo! been a chill day?",
        "hey there! everything good?",
        "sup! how you doing?",
        "hey! long day or chill one?",
        "yo, how you been?",
        "hey! what you up to?"
    ]

    options = [g for g in greetings if g != _last_greeting]
    if not options:
        options = greetings  

    chosen = random.choice(options)
    _last_greeting = chosen
    return chosen


def detect_empathy_needed(message: str) -> str:
    """
    Detect if user needs empathy/support.
    Returns: 'sad', 'excited', 'stressed', 'none'
    """
    message_lower = message.lower()
    

    sad_keywords = ['sad', 'down', 'depressed', 'upset', 'crying', 'failed', 
                    'lonely', 'miss', 'awful', 'terrible', 'worst', 'sucks']
    if any(word in message_lower for word in sad_keywords):
        return 'sad'
    

    excited_keywords = ['omg', 'yay', 'yes!!', 'amazing', 'excited', 'accepted',
                       'got it', 'won', 'passed', 'great news', '!!']
    if any(word in message_lower for word in excited_keywords) or message.count('!') >= 2:
        return 'excited'
   
    stress_keywords = ['stressed', 'anxious', 'worried', 'nervous', 'exam', 
                      'deadline', 'overwhelmed', 'pressure']
    if any(word in message_lower for word in stress_keywords):
        return 'stressed'
    
    return 'none'