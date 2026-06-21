# Matrix AI Agent

A FastAPI-based multi-channel AI chatbot for WhatsApp, Facebook, and Instagram. Handles customer conversations, lead collection, bookings, and conversation summaries.

---

## Project Structure

```
ai-agent/
├── agent/
│   ├── tools/
│   │   ├── collect_lead.py
│   │   ├── create_booking.py
│   │   ├── get_pricing.py
│   │   ├── handoff_human.py
│   │   ├── http_fallback.py
│   │   └── search_knowledge.py
│   ├── agent_runner.py
│   ├── memory.py
│   ├── prompt_builder.py
│   └── state.py
├── channels/
│   ├── facebook_sender.py
│   ├── instagram_sender.py
│   ├── router.py
│   └── whatsapp_sender.py
├── core/
│   ├── config.py
│   └── security.py
├── rag/
│   ├── ingestor.py
│   └── retriever.py
├── routes/
│   ├── agent_routes.py
│   └── summary_routes.py
├── summary_agent/
│   ├── scheduler.py
│   ├── summary_prompt.py
│   └── summary_runner.py
├── webhooks/
│   └── incoming.py
├── .env
├── main.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## Setup

### 1. Clone & create `.env`

```bash
For windows:
git clone https://github.com/faioperation/Roberto-Ai-Chatbot-Tareq.git
cd ai-agent
notepad .env
```

```bash
For server deployment:
git clone https://github.com/faioperation/Roberto-Ai-Chatbot-Tareq.git
cd Roberto-Ai-Chatbot-Tareq/ai-agent
touch .env
nano .env
```

`.env` required keys:
```
OPENAI_API_KEY=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=
ROBERTO_API_BASE=
ROBERTO_API_BASE_PUBLIC=
ROBERTO_API_TOKEN=
AGENT_API_TOKEN=
```

### 2. Run locally

```bash
- python -m venv venv
- Linux: source venv/bin/activate
- Windows: venv\Scripts\activate
- pip install -r requirements.txt
- python main.py
```

Server starts at `http://0.0.0.0:8005`

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8005
CMD ["python", "main.py"]
```

### docker-compose.yml

```yaml
version: "3.8"
services:
  ai-agent:
    build: .
    ports:
      - "8005:8005"
    env_file:
      - .env
    restart: unless-stopped
```

### .dockerignore

```
__pycache__
*.pyc
.env
venv
.git
```

### Deploy on server

```bash
# 1. Pull code
git clone <your-repo>
cd ai-agent

# 2. Create .env manually on the server
nano .env

# 3. Build and run
docker-compose up -d --build
```
---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/agent/message` | Receives incoming messages from backend |
| POST | `/api/agent/handoff` | Pause or resume AI for a conversation  |
| POST | `/api/summary/run`   | Manually trigger the summary job  |
| GET | `/api/summary/status` | Check conversations currently in memory  |

### Handoff payload

```json
{
  "business_id": "xxxx",
  "recipient_id": "xxxx",
  "action": "pause"
}
```
`action` values: `pause` or `resume`

---

## Booking Categories

Agent automatically decides the category from the conversation:

| Category | Use case |
|----------|----------|
| `CARGO_DELIVERY` | Physical parcel shipment |
| `APPOINTMENT_BOOKING` | Meeting / consultation / session |
| `ORDER_BOOKING` | Product / sales order |

---

## ⚠️ Important Warning Before Deployment

`requirements.txt` does not have exact versions pinned for `langgraph` and `langchain-openai`. During server build, the latest versions will be installed which may cause compatibility issues.

**Before deploying, run this command once locally:**

```bash
pip freeze > requirements.txt
```

This generates `requirements.txt` with exact versions — ensuring a stable Docker build.
