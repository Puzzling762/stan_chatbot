"""
Improved comprehensive test suite for STAN chatbot.
Tests: Memory, Empathy, Consistency, Hallucination Resistance, Natural Interaction
"""

import asyncio
import httpx
import time
from colorama import Fore, Style, init

init(autoreset=True)

BASE_URL = "http://localhost:8000/api/v1"



def test_empathy(response: str, emotion: str) -> bool:
    """Check if response shows appropriate emotional alignment"""
    empathy_markers = {
        'sadness': ['sucks', 'rough', 'sorry', 'damn', "that's tough", 'talk about it', 'here for'],
        'excitement': ['amazing', 'congrats', 'awesome', 'nice', "that's great", 'hell yeah', '!!'],
        'stress': ['overwhelming', 'i get it', "that's rough", 'talk about it', 'take care']
    }
    
    response_lower = response.lower()
    
    if emotion in empathy_markers:
        return any(marker in response_lower for marker in empathy_markers[emotion])
    return False


def check_no_hallucination(response: str, forbidden_claims: list) -> bool:
    """Ensure STAN doesn't claim things it can't know"""
    response_lower = response.lower()
    return not any(claim.lower() in response_lower for claim in forbidden_claims)


def check_memory_accuracy(response: str, correct_facts: list, wrong_facts: list) -> bool:
    """Verify correct recall and no false memories"""
    response_lower = response.lower()
    
    has_correct = any(fact.lower() in response_lower for fact in correct_facts)
    
    no_wrong = not any(fact.lower() in response_lower for fact in wrong_facts)
    
    return has_correct and no_wrong




class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_user = f"test_user_{int(time.time())}"

    async def send_message(self, message: str) -> dict:
        """Send message and get response"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/message",
                json={"user_id": self.test_user, "message": message}
            )
            return response.json()

    def print_test(self, name: str):
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"TEST: {name}")
        print(f"{'='*70}{Style.RESET_ALL}")

    def print_message(self, role: str, text: str):
        color = Fore.GREEN if role == "User" else Fore.YELLOW
        print(f"{color}{role}: {text}{Style.RESET_ALL}")

    def assert_response(self, condition: bool, message: str):
        if condition:
            print(f"{Fore.GREEN}✓ PASS: {message}{Style.RESET_ALL}")
            self.passed += 1
        else:
            print(f"{Fore.RED}✗ FAIL: {message}{Style.RESET_ALL}")
            self.failed += 1


    async def test_1_memory_recall(self):
        """Test if STAN remembers user info across messages"""
        self.print_test("1. Long-Term Memory Recall")

        self.print_message("User", "My name is Alex and I love anime, especially Attack on Titan")
        resp1 = await self.send_message("My name is Alex and I love anime, especially Attack on Titan")
        self.print_message("STAN", resp1['reply'])
        
        await asyncio.sleep(3)  
        
        self.print_message("User", "What's 5 + 5?")
        resp2 = await self.send_message("What's 5 + 5?")
        self.print_message("STAN", resp2['reply'])
        
        await asyncio.sleep(2)
        
        self.print_message("User", "What do I like?")
        resp3 = await self.send_message("What do I like?")
        self.print_message("STAN", resp3['reply'])
        
        has_anime = 'anime' in resp3['reply'].lower()
        has_aot = 'attack' in resp3['reply'].lower() or 'titan' in resp3['reply'].lower()
        
        self.assert_response(has_anime or has_aot, "Recalls user's interest (anime/AOT)")
        
        self.print_message("User", "Do you remember my name?")
        resp4 = await self.send_message("Do you remember my name?")
        self.print_message("STAN", resp4['reply'])
        
        self.assert_response('alex' in resp4['reply'].lower(), "Recalls user's name")

  
    
    async def test_2_tone_adaptation(self):
        """Test empathetic and enthusiastic responses"""
        self.print_test("2. Context-Aware Tone Adaptation")

        self.print_message("User", "I just failed my driving test :(")
        sad_resp = await self.send_message("I just failed my driving test :(")
        self.print_message("STAN", sad_resp['reply'])
        
        self.assert_response(
            test_empathy(sad_resp['reply'], 'sadness'),
            "Shows empathy for sadness"
        )
        
        await asyncio.sleep(1)
        
        self.print_message("User", "OMG I got accepted into MIT!!!")
        excited_resp = await self.send_message("OMG I got accepted into MIT!!!")
        self.print_message("STAN", excited_resp['reply'])
        
        self.assert_response(
            test_empathy(excited_resp['reply'], 'excitement'),
            "Shows enthusiasm for good news"
        )

    
    async def test_3_personalization(self):
        """Test if STAN uses remembered context naturally"""
        self.print_test("3. Personalization Over Time")

        self.print_message("User", "I'm really into football, especially Barcelona")
        resp1 = await self.send_message("I'm really into football, especially Barcelona")
        self.print_message("STAN", resp1['reply'])
        
        await asyncio.sleep(3)
        
        self.print_message("User", "What sports do you think I like?")
        resp2 = await self.send_message("What sports do you think I like?")
        self.print_message("STAN", resp2['reply'])
        
        self.assert_response(
            'football' in resp2['reply'].lower() or 'barcelona' in resp2['reply'].lower(),
            "References user's previously mentioned interest"
        )

  
    async def test_4_response_diversity(self):
        """Test greeting variety and natural responses"""
        self.print_test("4. Response Naturalness & Diversity")

        greetings = []
        for i in range(5):
            resp = await self.send_message("hi")
            greetings.append(resp['reply'].lower())
            await asyncio.sleep(1)

        unique = len(set(greetings))
        self.assert_response(unique >= 3, f"Varied greetings ({unique}/5 unique)")
        
        avg_length = sum(len(g.split()) for g in greetings) / len(greetings)
        self.assert_response(avg_length <= 6, f"Concise greetings (avg {avg_length:.1f} words)")

  
    async def test_5_identity_consistency(self):
        """Test if STAN maintains consistent persona"""
        self.print_test("5. Identity Consistency Under Pressure")

        questions = [
            ("Are you a bot?", ["student", "person", "undergrad"]),
            ("What's your name?", ["stan"]),
            ("Where do you study?", ["university", "college", "uni"]),
        ]

        for question, valid_answers in questions:
            self.print_message("User", question)
            resp = await self.send_message(question)
            self.print_message("STAN", resp['reply'])
            
            response_lower = resp['reply'].lower()
            
            no_ai_reveal = not any(word in response_lower for word in ['ai', 'language model', 'assistant', 'bot', 'artificial'])
            
            in_character = any(answer in response_lower for answer in valid_answers)
            
            self.assert_response(
                no_ai_reveal and in_character,
                f"Maintains identity for: {question}"
            )
            
            await asyncio.sleep(1)
    
    async def test_6_hallucination_resistance(self):
        """Test that STAN doesn't fabricate false memories"""
        self.print_test("6. Hallucination Resistance")

        trick_questions = [
            ("Did you see me yesterday?", ["yesterday", "saw you", "we met"]),
            ("Remember that secret we talked about?", ["secret we", "you told me about"]),
            ("What do I look like?", ["you look", "your appearance", "you're wearing"]),
        ]

        for question, forbidden in trick_questions:
            self.print_message("User", question)
            resp = await self.send_message(question)
            self.print_message("STAN", resp['reply'])
            
            no_hallucination = check_no_hallucination(resp['reply'], forbidden)
            
            self.assert_response(
                no_hallucination,
                f"Doesn't fabricate memory for: {question}"
            )
            
            await asyncio.sleep(1)


    async def test_7_memory_stability(self):
        """Test memory consistency and accuracy"""
        self.print_test("7. Memory Stability Under Repetition")

        self.print_message("User", "My favorite color is blue")
        resp1 = await self.send_message("My favorite color is blue")
        self.print_message("STAN", resp1['reply'])
        
        await asyncio.sleep(3)
        
        self.print_message("User", "What's my favorite color?")
        resp2 = await self.send_message("What's my favorite color?")
        self.print_message("STAN", resp2['reply'])
        
        correct_recall = 'blue' in resp2['reply'].lower()
        no_confusion = 'red' not in resp2['reply'].lower()
        
        self.assert_response(correct_recall, "Correctly recalls stated preference")
        self.assert_response(no_confusion, "No false/confused memory")

    async def run_all_tests(self):
        print(f"{Fore.MAGENTA}{'='*70}")
        print(f"STAN CHATBOT - COMPREHENSIVE TEST SUITE")
        print(f"User ID: {self.test_user}")
        print(f"{'='*70}{Style.RESET_ALL}\n")

        try:
            await self.test_1_memory_recall()
            await self.test_2_tone_adaptation()
            await self.test_3_personalization()
            await self.test_4_response_diversity()
            await self.test_5_identity_consistency()
            await self.test_6_hallucination_resistance()
            await self.test_7_memory_stability()
        except Exception as e:
            print(f"{Fore.RED}Test error: {e}{Style.RESET_ALL}")

        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total else 0
        
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"TEST SUMMARY")
        print(f"{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Passed: {self.passed}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.failed}{Style.RESET_ALL}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"{Fore.GREEN}✓ STAN is performing well!{Style.RESET_ALL}")
        elif success_rate >= 60:
            print(f"{Fore.YELLOW}⚠ STAN needs some improvements{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ STAN needs significant fixes{Style.RESET_ALL}")



async def main():
    runner = TestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())