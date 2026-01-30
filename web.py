from fastapi import FastAPI, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext
import json
import os
CRISIS_KEYWORDS = [
    "kill myself",
    "want to die",
    "end my life",
    "suicide",
    "self harm",
    "hurt myself",
    "cut myself",
    "no reason to live",
    "better off dead"
]

app = FastAPI()

# ---------- DATABASE ----------
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'echo.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

# ---------- SECURITY ----------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(pw):
    return pwd_context.hash(pw)

def verify_password(pw, hashed):
    return pwd_context.verify(pw, hashed)

# ---------- MEMORY ----------
MEMORY_FILE = "memory.json"
if os.path.exists(MEMORY_FILE):
    memory = json.load(open(MEMORY_FILE))
else:
    memory = {}

def save_memory():
    json.dump(memory, open(MEMORY_FILE, "w"), indent=2)

# ---------- MODELS ----------
class Chat(BaseModel):
    email: str
    text: str

# ---------- AI ----------
def fake_ai_reply(conversation):
    return (
        "I remember what you’ve shared earlier. "
        "You’re not starting over here. "
        "What feels most present for you right now?"
    )

# ---------- ROUTES ----------
@app.get("/", response_class=HTMLResponse)
def home():
    return open("index.html").read()

@app.post("/signup")
def signup(email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "User exists")

    user = User(email=email, password=hash_password(password))
    db.add(user)
    db.commit()
    return {"message": "Account created"}

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(401, "Invalid login")
    return {"email": email}

@app.post("/chat")
def chat(data: Chat):
    if data.email not in memory:
        memory[data.email] = []

    # Save user message
    memory[data.email].append(data.text)

    last_message = data.text.lower()

    # Crisis detection
    if any(keyword in last_message for keyword in CRISIS_KEYWORDS):
        reply = crisis_response()
    else:
        reply = fake_ai_reply(memory[data.email])

    # Save Echo reply
    memory[data.email].append(reply)
    save_memory()

    return {"reply": reply}

def crisis_response():
    return (
        "I’m really glad you told me this. I’m sorry you’re feeling so much pain. 💙\n\n"
        "I’m not able to help with anything that could hurt you, but I *do* want to help you stay safe.\n\n"
        "If you’re in immediate danger, please contact your local emergency number right now.\n\n"
        "You deserve support from a real person who can be with you in this moment.\n\n"
        "If you’re able to, consider reaching out to:\n"
        "• A trusted friend or family member\n"
        "• A mental health professional\n\n"
        "If you’re in India 🇮🇳:\n"
        "• AASRA: +91-9820466726 (24/7)\n"
        "• Kiran Helpline: 1800-599-0019\n\n"
        "If you’re elsewhere, you can find local crisis numbers at:\n"
        "https://findahelpline.com\n\n"
        "If you want, you can tell me where you are, and I can help find a local resource."
    )



