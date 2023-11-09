import json
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain.llms import OpenAI
from ..worker import LLMWorker

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={200: {"message": "success"}, 404: {"description": "Not found"}},
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

@router.get("/")
async def get_chat():
    return {"message": "Hello World!"}

@router.post("/")
async def chat(chat_params: ChatParams):
    print("chat_params")
    print(chat_params)
    chat_question = chat_params.userQuestion
    #print("chat_question")
    #print(chat_question)
    #conversation_history = chat_params.conversationHistory
    #print("conversation_history")
    #print(conversation_history)
    worker = LLMWorker()
    result = await worker.predict(chat_question)
    print("chat result")
    print(result)
    return result
