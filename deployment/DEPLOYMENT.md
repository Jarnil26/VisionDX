# VisionDX — Deployment Guide

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ (for frontend) |
| Docker & Docker Compose | 24+ |
| Tesseract OCR | 5+ |
| PostgreSQL | 15+ (or via Docker) |

---

## Option 1: Local Development (No Docker)

### 1. Clone and Set Up Python Environment

```bash
cd d:\risu\VisionDX

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env with your DB credentials, Tesseract path, etc.
```

> **Windows Tesseract path:** `TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe`
> Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki

### 3. Set Up PostgreSQL

```bash
# Create database
psql -U postgres
CREATE USER visiondx WITH PASSWORD 'visiondx_pass';
CREATE DATABASE visiondx OWNER visiondx;
\q
```

### 4. Train the ML Model

```bash
# Generate synthetic dataset
python -m visiondx.ml.generate_data

# Train RandomForest + XGBoost (picks best automatically)
python -m visiondx.ml.train_model
# Expected: >95% accuracy on synthetic data
```

### 5. Start the API Server

```bash
uvicorn visiondx.main:app --reload --port 8000
```

Open: **http://localhost:8000/docs** — Swagger UI with all endpoints

### 6. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open: **http://localhost:3000**

---

## Option 2: Docker Compose (Recommended)

### Full Stack Startup

```bash
cd d:\risu\VisionDX

# Copy and edit environment file
copy .env.example .env

# Build and start all services
docker-compose up --build

# In another terminal, run DB migrations and train model
docker-compose exec api python -m visiondx.ml.generate_data
docker-compose exec api python -m visiondx.ml.train_model
```

### Services

| Service | URL | Description |
|---------|-----|-------------|
| Nginx | http://localhost | Reverse proxy |
| FastAPI | http://localhost:8000 | Backend API |
| Swagger | http://localhost:8000/docs | API documentation |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache / task queue |

### Stop Services

```bash
docker-compose down
# With data cleanup:
docker-compose down -v
```

---

## API Example Requests

### Upload Report

```bash
curl -X POST http://localhost:8000/upload-report \
  -F "file=@blood_test.pdf" \
  -F "patient_phone=+919876543210"
```

**Response:**
```json
{
  "report_id": "VDX-20260306-AB12C3",
  "message": "Report processed successfully",
  "status": "done"
}
```

### Get Report

```bash
curl http://localhost:8000/report/VDX-20260306-AB12C3
```

**Response:**
```json
{
  "report_id": "VDX-20260306-AB12C3",
  "status": "done",
  "patient": { "name": "John Doe", "age": 35, "gender": "Male" },
  "parameters": [
    { "name": "Hemoglobin", "value": 10.2, "unit": "g/dL", "reference_range": "13-17", "status": "LOW" },
    { "name": "Glucose", "value": 95, "unit": "mg/dL", "reference_range": "70-100", "status": "NORMAL" }
  ]
}
```

### Get Disease Predictions

```bash
curl http://localhost:8000/report/VDX-20260306-AB12C3/prediction
```

**Response:**
```json
{
  "report_id": "VDX-20260306-AB12C3",
  "possible_conditions": [
    { "disease": "Anemia", "confidence": 0.87 },
    { "disease": "Iron Deficiency", "confidence": 0.73 },
    { "disease": "Normal", "confidence": 0.05 }
  ]
}
```

### Get Abnormal Analysis

```bash
curl http://localhost:8000/report/VDX-20260306-AB12C3/analysis
```

**Response:**
```json
{
  "report_id": "VDX-20260306-AB12C3",
  "total_parameters": 12,
  "abnormal_count": 3,
  "normal_count": 9,
  "summary": "Out of 12 tested parameters, 3 value(s) are outside the normal range. Below normal (LOW): Hemoglobin, RBC. Elevated (HIGH): Glucose. Based on the AI analysis, results may suggest: Anemia (87% probability)...",
  "parameters": [ ... ]
}
```

### Doctor Lookup

```bash
curl http://localhost:8000/doctor/report/VDX-20260306-AB12C3
```

---

## Running Tests

```bash
cd d:\risu\VisionDX

# Activate virtual environment first
pip install pytest pytest-asyncio

# Run all unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=visiondx --cov-report=term-missing
```

---

## Architecture: Microservice Version (Future)

For scaling beyond a single server, split into these independent services:

```
visiondx-gateway    → Nginx/Kong API gateway
visiondx-ocr        → PDF ingestion & OCR (GPU optional)
visiondx-parser     → Medical parameter extraction
visiondx-predictor  → ML model inference (scale independently)
visiondx-notifier   → WhatsApp delivery worker
visiondx-api        → FastAPI REST layer
visiondx-frontend   → Next.js dashboard
```

Each communicates via Redis Pub/Sub or Kafka message queues.

---

## Security Notes (HIPAA-Style)

- All patient data stored encrypted at rest (PostgreSQL column encryption recommended for production)
- JWT tokens expire after 60 minutes
- HTTPS enforced via Nginx in production (add SSL certificate)
- Upload files stored with UUID filenames (no patient info in path)
- Add rate limiting to `/upload-report` to prevent abuse
- Never log raw patient data

---

## Future Roadmap

| Feature | Description |
|---------|-------------|
| AI Report Explanation | LLM-powered natural language explanation of results |
| Medical Chatbot | Patient Q&A about their report |
| Doctor Recommendation | Suggest nearest specialist based on prediction |
| Health Risk Scoring | 0-100 composite risk score |
| Multilingual Support | Tamil, Hindi, Bengali report parsing |
| Deep Neural Network | Replace RF/XGBoost with fine-tuned medical DNN |
| ABDM Integration | India's Ayushman Bharat Digital Mission compliance |
