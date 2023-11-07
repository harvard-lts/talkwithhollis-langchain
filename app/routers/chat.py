import json
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain.llms import OpenAI
llm = OpenAI(temperature=0)

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
    qs_prompt_formatted_str = "You are a helpful assistant that answers general questions about anything. \n\nUser question: "
    qs_prompt_formatted_str += chat_question.user_input
    print("qs_prompt_formatted_str")
    print(qs_prompt_formatted_str)
    qs_prediction = llm.predict(qs_prompt_formatted_str)

    # print the prediction
    print("qs_prediction")
    print(qs_prediction)
    #qs_prompt_result = json.loads(qs_prediction)
    #print("qs_prompt_result")
    #print(qs_prompt_result)
    return qs_prediction
