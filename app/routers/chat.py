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

class ChatQuestion(BaseModel):
    user_input: str

app = FastAPI()

@router.get("/")
async def get_chat():
    return {"message": "Hello World!"}

@router.post("/")
async def chat(chat_question: ChatQuestion):
    print("chat_question")
    print(chat_question)
    worker = LLMWorker()
    result = await worker.predict(chat_question)
    return result

