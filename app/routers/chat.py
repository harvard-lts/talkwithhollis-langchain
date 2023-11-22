import json
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain.llms import OpenAI
from ..worker import LLMWorker
from ..utils.libcalutils import LibCalUtils

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"]
    #responses={200: {"message": "success"}, 404: {"description": "Not found"}},
)

"""
{
    "conversationHistory": [
        {
            "user": "test1",
            "assistant": "This is a response to the test1."
        },
        {
            "user": "test2",
            "assistant": "This is a response to the test2."
        }
    ],
    "userQuestion": "test3"
}
"""
class ConversationHistoryInstance(BaseModel):
    user: str
    assistant: str

class ChatParams(BaseModel):
    userQuestion: str
    conversationHistory: list[ConversationHistoryInstance]

class Message(BaseModel):
    role: str
    content: str

class ChatResult(BaseModel):
    message: Message

@router.get("/")
async def get_chat():
    return {"message": "Hello World!"}

@router.post("/")
async def chat(chat_params: ChatParams) -> ChatResult:
    chat_question = chat_params.userQuestion
    conversation_history = chat_params.conversationHistory
    # worker = LLMWorker()
    worker = LibCalUtils()
    # result = await worker.predict(chat_question, conversation_history)
    # chat_result: ChatResult = {
    #   "message": {
    #     "role": "assistant",
    #     "content": result
    #   }
    # }
    # print("chat result")
    # print(chat_result)
    return 'abc123'
