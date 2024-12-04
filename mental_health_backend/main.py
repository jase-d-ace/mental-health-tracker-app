from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from .schemas.journal import Journal
from .models import models
from .settings import OPENAI_API_KEY # if this apikey is on github, you're totally cooked. Please triple check settings has not been committed. Please.
from .db import engine, get_db
from .models.models import Base
from sqlalchemy.orm import Session
import logging

app = FastAPI()
client = OpenAI(api_key=OPENAI_API_KEY)
Base.metadata.create_all(bind=engine)


origins = [
    "http://localhost:3000",
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "hello": "world",
        "foo": "bar"
    }

@app.post("/journal", response_model=Journal)
async def handle_entry(request: Request, db: Session = Depends(get_db)):
    req = await request.json()

    emotions_map = {
        -2: "I feel awful",
        -1: "I don't feel great",
        0: "I feel neutral or I'm having trouble feeling at all",
        1: "I actually feel okay",
        2: "I feel incredible"
    }

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You will receive three pieces of information: a Feeling, a Title, and an Entry. Please respond to the entry and feeling as someone who cares about the writer's mental wellbeing, and provide affirmations, advice, and any relevant mental health reminders. There's no need to lead with a greeting, please just get right into the advice."},
            {"role": "user", "content": f"Today: {emotions_map[req['feeling']]}\nTitle: {req['title']}\nEntry: {req['content']}"}
        ],
        temperature=0.7
    )

    new_entry = models.Journal(
        title=req["title"],
        feeling=req["feeling"],
        content=req["content"],
        answer=completion.choices[0].message.content
    )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return {
        "id": new_entry.id,
        "published_at": new_entry.published_at,
        "title": new_entry.title,
        "feeling": new_entry.feeling,
        "content": new_entry.content,
        "answer": new_entry.answer,
        "user_id": "ab70d1c1-d1ce-485c-8c2e-786a9345ceff"
    }

@app.get("/journals")
def get_journals(db: Session = Depends(get_db)):
    journals = db.query(models.Journal)

    return {
        "journals": journals.all()
    }


@app.post("/users/register")
async def create_user(request: Request, db: Session = Depends(get_db)):
    req = await request.json()
    db_user = db.query(models.User).filter(models.User.username == req["username"]).first()
    if db_user:
        return {
            "status": "already registered, but how did you get here?"
        }
    new_user = models.User(username=req["username"])
    new_user.set_password(req["password"])
    db.add(new_user)
    db.commit()
    return {
        "username": new_user.username,
        "id": new_user.id
    }