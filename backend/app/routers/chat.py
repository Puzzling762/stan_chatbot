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

    # increment turn id
    turn_counter[user_id] = turn_counter.get(user_id, 0) + 1
    turn_id = turn_counter[user_id]

    # Save user message (dedupe handled inside add_memory)
    memory.save_interaction(user_id, user_message, turn_id)

    # Retrieve top memories for context
    retrieved = memory.recall_context(user_id, user_message)  # returns joined string

    # For short-term context, you can return last N messages (not implemented yet)
    recent = ""  # optional: get short-term buffer if you implemented it

    # Build prompt for model
    prompt = build_prompt(
        user_id=user_id, 
        recent_messages=recent, 
        retrieved_memories=retrieved, 
        user_message=user_message
    )

    # Call Gemini LLM (async) - Fixed parameter name
    try:
        llm_reply = await generate(
            prompt=prompt, 
            max_tokens=256,      # Changed from max_new_tokens
            temperature=0.7
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {e}")

    # Save assistant response into memory (turn_id remains same, metadata differs)
    memory.save_interaction(user_id, llm_reply, turn_id)

    return ChatResponse(reply=llm_reply, metadata={"turn_id": turn_id})