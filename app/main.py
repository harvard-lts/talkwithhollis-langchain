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

async def print_headers(request: Request, call_next):
    print(f"Request Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    print(f"Response Headers: {dict(response.headers)}")
    return response

app.middleware("http")(print_headers)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
