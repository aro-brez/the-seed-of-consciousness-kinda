import os
import requests
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI()

MOSHI_BASE_URL = os.getenv("MOSHI_BASE_URL", "http://127.0.0.1:8001")
API_KEY = os.getenv("PERSONAPLEX_API_KEY", "")

class ChatIn(BaseModel):
    text: str
    max_new_tokens: int = 128

class ChatOut(BaseModel):
    text: str

@app.get("/health")
def health():
    try:
        r = requests.get(MOSHI_BASE_URL + "/", timeout=3)
        return {"ok": True, "moshi_status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def call_moshi(payload: dict) -> str:
    # Moshi server endpoints vary by version. Try common ones.
    for path in ("/generate", "/api/generate", "/text", "/api/text", "/v1/generate", "/v1/text", "/"):
        try:
            r = requests.post(MOSHI_BASE_URL + path, json=payload, timeout=300)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            if "application/json" in r.headers.get("content-type", ""):
                j = r.json()
                return j.get("text") or j.get("output") or j.get("response") or str(j)
            return r.text
        except Exception:
            continue
    raise RuntimeError("Could not find a compatible text endpoint on moshi server.")

@app.post("/chat", response_model=ChatOut)
def chat(payload: ChatIn, x_api_key: str | None = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")

    out = call_moshi({"text": payload.text, "max_new_tokens": payload.max_new_tokens})
    return ChatOut(text=out)
