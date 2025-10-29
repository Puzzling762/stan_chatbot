# app/core/llm_client.py
import os
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()  # gemini, claude, groq, cohere

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-20241022")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
COHERE_MODEL = os.getenv("COHERE_MODEL", "command-r-08-2024")


PROVIDER_LIMITS = {
    "gemini": {
        "rpm": 15,          
        "rpd": 1500,        
        "tpm": 1_000_000,   
        "name": "Gemini 2.0 Flash"
    },
    "claude": {
        "rpm": 50,
        "rpd": 100_000,  
        "tpm": 40_000,
        "name": "Claude 3.5 Haiku"
    },
    "groq": {
        "rpm": 30,
        "rpd": 14_400,
        "tpm": 20_000,
        "name": "Groq Llama 3.3 70B"
    },
    "cohere": {
        "rpm": 10,
        "rpd": 10_000,
        "tpm": 10_000,
        "name": "Cohere Command R"
    }
}

class UsageTracker:
    """Track API usage to warn before hitting limits"""
    def __init__(self):
        self.daily_count = 0
        self.minute_count = 0
        self.last_reset = datetime.now()
        self.minute_reset = datetime.now()
    
    def log_request(self):
        now = datetime.now()
        
    
        if (now - self.last_reset).days >= 1:
            self.daily_count = 0
            self.last_reset = now
        
        
        if (now - self.minute_reset).seconds >= 60:
            self.minute_count = 0
            self.minute_reset = now
        
        self.daily_count += 1
        self.minute_count += 1
        
        
        limits = PROVIDER_LIMITS.get(PROVIDER, {})
        rpd = limits.get("rpd", 1000)
        rpm = limits.get("rpm", 10)
        
        
        daily_remaining = rpd - self.daily_count
        minute_remaining = rpm - self.minute_count
        
        
        if self.daily_count % 100 == 0:  
            print(f"📊 Usage: {self.daily_count}/{rpd} requests today ({daily_remaining} left)")
        
        if daily_remaining < 50:
            print(f"⚠️  WARNING: Only {daily_remaining} requests left today!")
        
        if minute_remaining < 3:
            print(f"⚠️  Near rate limit: {minute_remaining} requests left this minute")
        
        return {
            "daily_used": self.daily_count,
            "daily_remaining": daily_remaining,
            "minute_remaining": minute_remaining
        }

usage_tracker = UsageTracker()


class RateLimiter:
    def __init__(self):
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        async with self.lock:
            limits = PROVIDER_LIMITS.get(PROVIDER, {"rpm": 10})
            max_requests = limits["rpm"] - 2  
            
            now = datetime.now()
            self.requests = [t for t in self.requests 
                           if now - t < timedelta(seconds=60)]
            
            if len(self.requests) < max_requests:
                self.requests.append(now)
                return True
            
            oldest = self.requests[0]
            wait_time = (oldest + timedelta(seconds=60) - now).total_seconds()
            
            if wait_time > 0:
                print(f"⏳ Rate limit, waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time + 0.2)
            
            self.requests.append(now)
            return True

rate_limiter = RateLimiter()


async def web_search(query: str, num_results: int = 3) -> str:
    """Search the web using Serper API"""
    if not SERPER_API_KEY:
        return ""
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": SERPER_API_KEY,
                    "Content-Type": "application/json"
                },
                json={"q": query, "num": num_results}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                answer = data.get("answerBox", {})
                if answer:
                    snippet = answer.get("answer") or answer.get("snippet", "")
                    if snippet:
                        return f"[Web]: {snippet}\n"
                
                results = []
                for item in data.get("organic", [])[:2]:
                    snippet = item.get("snippet", "")
                    if snippet:
                        results.append(f"• {snippet}")
                
                if results:
                    return "[Search Results]:\n" + "\n".join(results) + "\n"
                
            return ""
    except Exception as e:
        print(f"[Search Error]: {e}")
        return ""

def needs_search(message: str) -> bool:
    """Check if message needs web search"""
    message_lower = message.lower().strip()
    
    explicit_search = [
        'do you know about', 'tell me about', 'what do you know about',
        'have you heard of', 'info about', 'information about',
        'explain', 'who is', 'what is', 'when was', 'where is', 'how did'
    ]
    
    return any(phrase in message_lower for phrase in explicit_search)


async def _call_gemini(prompt: str, max_tokens: int, temperature: float, timeout: int) -> str:
    """Call Gemini API"""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    params = {"key": GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "topP": 0.95,
            "topK": 40,
        },
        "safetySettings": [
            {"category": cat, "threshold": "BLOCK_ONLY_HIGH"}
            for cat in [
                "HARM_CATEGORY_HARASSMENT",
                "HARM_CATEGORY_HATE_SPEECH", 
                "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "HARM_CATEGORY_DANGEROUS_CONTENT"
            ]
        ]
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, params=params, json=payload)
        
        if resp.status_code == 429:
            return None  
        
        resp.raise_for_status()
        data = resp.json()
        
        candidates = data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"].strip()
    
    return "Could you rephrase that?"

async def _call_claude(prompt: str, max_tokens: int, temperature: float, timeout: int) -> str:
    """Call Claude API"""
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
        
        if resp.status_code == 429:
            return None
        
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("content"):
            return data["content"][0]["text"].strip()
    
    return "Could you rephrase that?"

async def _call_groq(prompt: str, max_tokens: int, temperature: float, timeout: int) -> str:
    """Call Groq API"""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
        
        if resp.status_code == 429:
            return None
        
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("choices"):
            return data["choices"][0]["message"]["content"].strip()
    
    return "Could you rephrase that?"

async def _call_cohere(prompt: str, max_tokens: int, temperature: float, timeout: int) -> str:
    """Call Cohere API"""
    if not COHERE_API_KEY:
        raise RuntimeError("COHERE_API_KEY not set")
    
    url = "https://api.cohere.ai/v1/chat"
    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": COHERE_MODEL,
        "message": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
        
        if resp.status_code == 429:
            return None
        
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("text"):
            return data["text"].strip()
    
    return "Could you rephrase that?"



async def generate(
    prompt: str,
    user_message: str = "",
    max_tokens: int = 350,
    temperature: float = 0.9,
    timeout_seconds: int = 30,
    enable_search: bool = True
) -> str:
    """
    Generate text using configured LLM provider.
    Automatically tracks usage and switches providers if needed.
    """
    
    provider_info = PROVIDER_LIMITS.get(PROVIDER, {})
    provider_name = provider_info.get("name", PROVIDER)
    
    search_results = ""
    if enable_search and user_message and needs_search(user_message):
        print(f"🔍 Searching: {user_message}")
        search_results = await web_search(user_message)
        
        if search_results:
            prompt = prompt.replace("STAN:", f"{search_results}\nSTAN:")
    
    usage = usage_tracker.log_request()
    
    await rate_limiter.acquire()
    
    provider_func = {
        "gemini": _call_gemini,
        "claude": _call_claude,
        "groq": _call_groq,
        "cohere": _call_cohere
    }.get(PROVIDER)
    
    if not provider_func:
        raise RuntimeError(f"Unknown provider: {PROVIDER}")
    
    for attempt in range(2):
        try:
            result = await provider_func(prompt, max_tokens, temperature, timeout_seconds)
            
            if result is None:  
                if attempt == 0:
                    print("⏳ Rate limit hit, waiting 3s...")
                    await asyncio.sleep(3)
                    continue
                return "Whoa, slow down a bit! Give me a sec and try again 😅"
            
            return result
        
        except httpx.TimeoutException:
            if attempt == 0:
                print("⏳ Timeout, retrying once...")
                await asyncio.sleep(1)
                continue
            return "Taking too long to think... try asking again!"
        
        except Exception as e:
            print(f"❌ Error with {provider_name}: {e}")
            if attempt == 0:
                await asyncio.sleep(1)
                continue
            return "Oops, something went wrong on my end. Try again?"
    
    return "Having some trouble right now. Give me a moment!"


def print_provider_info():
    """Print current provider info on startup"""
    provider_info = PROVIDER_LIMITS.get(PROVIDER, {})
    name = provider_info.get("name", PROVIDER)
    rpm = provider_info.get("rpm", "Unknown")
    rpd = provider_info.get("rpd", "Unknown")
    
    print(f"""
╔══════════════════════════════════════╗
║     LLM PROVIDER CONFIGURATION       ║
╠══════════════════════════════════════╣
║ Provider: {name:<26} ║
║ Limits:   {rpm} req/min, {rpd} req/day   ║
║ Model:    {PROVIDER}                        ║
╚══════════════════════════════════════╝
    """)


print_provider_info()