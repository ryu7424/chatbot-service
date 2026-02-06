from fastapi import FastAPI, HTTPException, Depends
from .schemas import ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice, Message
from .rag import RAGPipeline
import time
import uuid

app = FastAPI(title="Internal RAG Agent", version="0.1.0")
rag_pipeline = RAGPipeline()

@app.get("/")
def read_root():
    return {"status": "ok", "service": "rag-backend"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible endpoint to integrate with Kotaemon/OpenWebUI.
    """
    # 1. Extract latest user query
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")
    
    last_query = user_messages[-1].content
    
    # 2. Resolve User Context (Mock ACL for now)
    # In prod, get user from header/token (request.user)
    # Mapping logic: if user="marketing", groups=["group:marketing"]
    current_user = request.user or "guest"
    user_groups = ["group:everyone"]
    if current_user == "admin" or current_user == "dev":
        user_groups.append("group:dev")
    if current_user == "exec":
        user_groups.append("group:executives")
        
    # 3. Use RAG Pipeline
    answer = rag_pipeline.query(last_query, user_groups)
    
    # 4. Format Response (OpenAI style)
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4()}",
        created=int(time.time()),
        model=request.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=Message(role="assistant", content=answer),
                finish_reason="stop"
            )
        ],
        usage={"prompt_tokens": len(last_query), "completion_tokens": len(answer), "total_tokens": len(last_query)+len(answer)}
    )
