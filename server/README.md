# SEED Server - PersonaPlex/Moshi API

FastAPI wrapper for the PersonaPlex-7B/Moshi full-duplex speech model.

## Architecture

```
brez-os (Next.js)
    └── /api/personaplex/route.ts
            ↓ HTTP
GPU Server (Lambda @ 209.20.159.84)
    └── ~/the-seed-of-consciousness-kinda/server/app.py (this file)
            ↓ Internal
    └── Moshi model (localhost:8001)
```

## Setup on GPU Server

### 1. SSH into the Lambda server

```bash
ssh -i ~/.ssh/brez-os-gpu.pem ubuntu@209.20.159.84
```

### 2. Navigate to the repo

```bash
cd ~/the-seed-of-consciousness-kinda
```

### 3. Create/activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Set environment variables

```bash
export MOSHI_BASE_URL=http://127.0.0.1:8001  # Where Moshi is running
export PERSONAPLEX_API_KEY=your-secret-key   # Optional: protect the endpoint
```

### 5. Start the server

```bash
cd server
uvicorn app:app --host 0.0.0.0 --port 8000
```

Or with auto-reload for development:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

### `GET /health`
Check if server and Moshi are running.

**Response:**
```json
{
  "ok": true,
  "moshi_status": 200
}
```

### `POST /chat`
Send text, get response from Moshi.

**Request:**
```json
{
  "text": "Hello, how are you?",
  "max_new_tokens": 128
}
```

**Headers (if API key is set):**
```
X-API-Key: your-secret-key
```

**Response:**
```json
{
  "text": "I'm doing well! How can I help you today?"
}
```

## Testing

```bash
# Health check
curl http://209.20.159.84:8000/health

# Chat (from anywhere)
curl -X POST http://209.20.159.84:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello!"}'
```

## Security Notes

- The server binds to `0.0.0.0` (all interfaces) - ensure firewall rules are configured
- Use `PERSONAPLEX_API_KEY` to protect the endpoint in production
- Consider adding rate limiting for public deployments

## Connection from BREZ OS

In brez-os, add to `.env.local`:
```
PERSONAPLEX_SERVER_URL=http://209.20.159.84:8000
PERSONAPLEX_API_KEY=your-api-key-if-set
```

Then call `/api/personaplex` from the frontend:
```typescript
// Health check
const health = await fetch('/api/personaplex');

// Chat
const response = await fetch('/api/personaplex', {
  method: 'POST',
  body: JSON.stringify({ text: 'Hello!' })
});
```
