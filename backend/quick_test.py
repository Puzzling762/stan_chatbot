"""
Quick test to verify speed and search functionality
"""

import asyncio
import httpx
import time
from colorama import Fore, Style, init

init(autoreset=True)

BASE_URL = "http://localhost:8000/api/v1"

async def test_message(message: str, user_id: str = "speed_test"):
    """Send message and measure response time"""
    start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/message",
                json={"user_id": user_id, "message": message}
            )
            
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                reply = data['reply']
                
                print(f"\n{Fore.GREEN}You: {message}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}STAN: {reply}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}⏱️  Response time: {elapsed:.2f}s{Style.RESET_ALL}")
                return elapsed
            else:
                print(f"{Fore.RED}Error {response.status_code}: {response.text}{Style.RESET_ALL}")
                return None
    
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return None

async def run_tests():
    """Run speed and functionality tests"""
    
    print(f"{Fore.MAGENTA}{'='*70}")
    print("⚡ STAN CHATBOT - SPEED & SEARCH TEST")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}TEST 1: Basic Greeting (No Search){Style.RESET_ALL}")
    t1 = await test_message("hey there!")
    await asyncio.sleep(2)
    
    print(f"\n{Fore.CYAN}TEST 2: Casual Chat (No Search){Style.RESET_ALL}")
    t2 = await test_message("I'm feeling kinda down today")
    await asyncio.sleep(2)
    
    print(f"\n{Fore.CYAN}TEST 3: Preference (No Search){Style.RESET_ALL}")
    t3 = await test_message("i love anime")
    await asyncio.sleep(2)
    
    print(f"\n{Fore.CYAN}TEST 4: Explicit Search Query (SHOULD Search){Style.RESET_ALL}")
    t4 = await test_message("do you know about real madrid")
    await asyncio.sleep(2)
    
    print(f"\n{Fore.CYAN}TEST 5: Another Search Query{Style.RESET_ALL}")
    t5 = await test_message("tell me about attack on titan anime")
    await asyncio.sleep(2)
    
    print(f"\n{Fore.CYAN}TEST 6: Regular Question (No Search){Style.RESET_ALL}")
    t6 = await test_message("what anime do you like?")
    
    print(f"\n{Fore.MAGENTA}{'='*70}")
    print("📊 PERFORMANCE SUMMARY")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    times = [t for t in [t1, t2, t3, t4, t5, t6] if t is not None]
    
    if times:
        avg = sum(times) / len(times)
        print(f"{Fore.GREEN}Average Response Time: {avg:.2f}s{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Fastest: {min(times):.2f}s{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Slowest: {max(times):.2f}s{Style.RESET_ALL}")
        
        if avg < 3:
            print(f"\n{Fore.GREEN}✅ EXCELLENT: Very fast responses!{Style.RESET_ALL}")
        elif avg < 5:
            print(f"\n{Fore.YELLOW}✅ GOOD: Acceptable speed{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}⚠️  SLOW: Consider checking API rate limits{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}💡 Tips:")
    print("- Search queries (with 'do you know about') will be 2-3s slower")
    print("- Regular chat should be under 2-3 seconds")
    print("- If slow, check rate limits and server load{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")