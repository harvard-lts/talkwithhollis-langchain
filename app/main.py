from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat
from fastapi import Request, Response

app = FastAPI()

origins = [
    "http://localhost:3000",
]

# https://fastapi.tiangolo.com/tutorial/cors/
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
