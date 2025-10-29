# chat_interactive.py
"""
Enhanced interactive chat client for STAN chatbot
with better error handling and user experience
"""

import asyncio
import httpx
from colorama import Fore, Style, init
import sys

init(autoreset=True)

BASE_URL = "http://localhost:8000/api/v1"

class ChatClient:
    def __init__(self):
        self.user_id = None
        self.session_active = False
    
    async def send_message(self, message: str) -> dict:
        """Send message with timeout and retry logic."""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{BASE_URL}/message",
                        json={"user_id": self.user_id, "message": message}
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 429:
                        print(f"{Fore.YELLOW}⏳ Rate limit hit, waiting...{Style.RESET_ALL}")
                        await asyncio.sleep(5)
                        continue
                    else:
                        return {"error": f"HTTP {response.status_code}: {response.text}"}
            
            except httpx.TimeoutException:
                print(f"{Fore.YELLOW}⏳ Request timeout, retrying...{Style.RESET_ALL}")
                await asyncio.sleep(2)
            except Exception as e:
                return {"error": str(e)}
        
        return {"error": "Max retries exceeded"}
    
    async def check_connection(self):
        """Check if server is running."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8000/")
                if response.status_code == 200:
                    return True
        except:
            return False
        return False
    
    def print_header(self):
        """Print welcome header."""
        print(f"{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.CYAN}   ███████╗████████╗ █████╗ ███╗   ██╗")
        print(f"   ██╔════╝╚══██╔══╝██╔══██╗████╗  ██║")
        print(f"   ███████╗   ██║   ███████║██╔██╗ ██║")
        print(f"   ╚════██║   ██║   ██╔══██║██║╚██╗██║")
        print(f"   ███████║   ██║   ██║  ██║██║ ╚████║")
        print(f"   ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Your friendly AI companion for authentic conversations{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}\n")
    
    async def start_session(self):
        """Start interactive chat session."""
        self.print_header()
        
        print(f"{Fore.YELLOW}Checking server connection...{Style.RESET_ALL}")
        if not await self.check_connection():
            print(f"{Fore.RED}❌ Cannot connect to server at {BASE_URL}")
            print(f"Make sure the FastAPI server is running:")
            print(f"   cd backend && uvicorn app.main:app --reload{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}✓ Server connected!{Style.RESET_ALL}\n")
        
        while not self.user_id:
            user_input = input(f"{Fore.CYAN}Enter your name/username: {Style.RESET_ALL}").strip()
            if user_input:
                self.user_id = user_input
                print(f"{Fore.GREEN}✓ Logged in as: {self.user_id}{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}💬 Start chatting! Commands:")
        print(f"   • Type 'quit' or 'exit' to leave")
        print(f"   • Type 'reset' to clear conversation history")
        print(f"   • Type 'clear' to clear screen{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'-'*70}{Style.RESET_ALL}\n")
        
        self.session_active = True
        
        while self.session_active:
            try:
                user_input = input(f"{Fore.GREEN}{self.user_id}: {Style.RESET_ALL}").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print(f"\n{Fore.CYAN}👋 STAN: Catch you later! Take care!{Style.RESET_ALL}\n")
                    self.session_active = False
                    break
                
                elif user_input.lower() == 'reset':
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            await client.post(f"{BASE_URL}/reset", params={"user_id": self.user_id})
                        print(f"{Fore.YELLOW}🔄 Conversation history cleared{Style.RESET_ALL}\n")
                    except Exception as e:
                        print(f"{Fore.RED}Failed to reset: {e}{Style.RESET_ALL}\n")
                    continue
                
                elif user_input.lower() == 'clear':
                    print("\n" * 50)
                    self.print_header()
                    continue
                
                response = await self.send_message(user_input)
                
                if 'error' in response:
                    print(f"{Fore.RED}❌ Error: {response['error']}{Style.RESET_ALL}\n")
                else:
                    reply = response.get('reply', 'No response')
                    print(f"{Fore.CYAN}🤖 STAN: {Style.RESET_ALL}{reply}\n")
            
            except KeyboardInterrupt:
                print(f"\n\n{Fore.CYAN}👋 STAN: Interrupted. See you later!{Style.RESET_ALL}\n")
                self.session_active = False
                break
            
            except Exception as e:
                print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}\n")

async def main():
    """Main entry point."""
    client = ChatClient()
    await client.start_session()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)