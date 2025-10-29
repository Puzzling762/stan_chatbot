# app/routers/chat.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.core.memory_manager import MemoryManager
from app.core.prompt_templates import build_prompt
from app.core.llm_client import generate

router = APIRouter(prefix="/api/v1", tags=["Chat"])
memory = MemoryManager()
turn_counter: dict = {}

@router.post("/message", response_model=ChatResponse)
async def handle_message(request: ChatRequest):
    user_id = request.user_id
    user_message = request.message

    turn_counter[user_id] = turn_counter.get(user_id, 0) + 1
    turn_id = turn_counter[user_id]

    # Save user message
    memory.save_interaction(user_id, user_message, turn_id, is_user=True)

    # Get relevant memories (increase from 2 to 4 for better recall)
    retrieved = memory.recall_context(user_id, user_message, top_k=6)  

    # FIXED: Actually get recent conversation context
    recent = memory.get_recent_context(user_id)
    
    prompt = build_prompt(
        user_id=user_id, 
        recent_messages=recent, 
        retrieved_memories=retrieved, 
        user_message=user_message
    )

    try:
        llm_reply = await generate(
            prompt=prompt, 
            user_message=user_message,  # Pass for search detection
            max_tokens=256,      
            temperature=0.7
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {e}")

    # Save STAN's response
    memory.save_interaction(user_id, llm_reply, turn_id, is_user=False)

    return ChatResponse(reply=llm_reply, metadata={"turn_id": turn_id})

@router.post("/reset")
async def reset_conversation(user_id: str):
    """Reset conversation memory for a user"""
    memory.clear_session(user_id)
    return {"message": f"Conversation reset for {user_id}"}