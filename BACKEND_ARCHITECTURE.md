# VisionDX Backend Architecture - Implementation Guide

## 📋 Overview

This document outlines the comprehensive backend architecture for VisionDX with production-grade modules.

## 🏗️ Project Structure

```
visiondx/
├── api/
│   ├── __init__.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py              # JWT & API key auth
│   │   └── error_handlers.py    # Global exception handling
│   └── routes/
│       ├── __init__.py
│       ├── auth.py              # User registration & login
│       ├── users.py             # User profile & health data
│       ├── labs.py              # Lab management & bookings
│       ├── reports.py           # Report upload & retrieval
│       ├── follow_ups.py         # Weekly & monthly follow-ups
│       ├── chat.py              # AI Chat Doctor (text & voice)
│       ├── doctor.py            # Doctor dashboard
│       └── developer.py          # Developer API keys
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py          # Auth logic, JWT tokens
│   ├── user_service.py          # User profile management
│   ├── lab_service.py           # Lab booking logic
│   ├── report_service.py        # Report processing
│   ├── follow_up_service.py     # Health tracking
│   ├── chat_service.py          # AI Chat logic
│   ├── prediction_service.py    # ML predictions
│   ├── location_service.py      # Geo-search (doctors, hospitals)
│   └── notification_service.py  # Email, SMS notifications
│
├── ml/
│   ├── __init__.py
│   ├── symptom_classifier.py    # Classify symptoms
│   ├── trend_analyzer.py        # Time-series trend analysis
│   ├── risk_scorer.py           # Risk scoring (0-100)
│   ├── health_predictor.py      # Predict health conditions
│   ├── anomaly_detector.py      # Detect abnormal trends
│   └── models/
│       ├── symptom_classifier.pkl
│       ├── trend_model.pkl
│       └── risk_model.pkl
│
├── database/
│   ├── __init__.py
│   ├── connection.py            # DB connection setup
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic request/response schemas
│   └── migrations/
│       └── alembic/             # Alembic migrations
│
├── utils/
│   ├── __init__.py
│   ├── security.py              # Password hashing, JWT
│   ├── validators.py            # Input validation
│   ├── formatting.py            # Data formatting
│   ├── logger.py                # Structured logging
│   └── constants.py             # Constants & enums
│
├── core/
│   ├── __init__.py
│   ├── exceptions.py            # Custom exceptions
│   ├── dependencies.py          # FastAPI dependencies
│   └── config.py                # Internal config
│
├── config.py                     # Environment settings
├── main.py                       # FastAPI app
├── startup.py                    # Startup hooks
└── worker.py                     # Background tasks (Celery)
```

## 🔑 Core Modules

### 1. **Authentication & Authorization**
- JWT token generation & validation
- Password hashing (bcrypt)
- OAuth2 password flow
- Role-based access control (RBAC)
- API key authentication (for labs)

### 2. **User Management**
- User registration (email/phone)
- Profile management
- Medical history tracking
- Language preferences
- Subscription/plan management

### 3. **Lab Collaboration**
- Lab partner registration
- Lab API authentication
- Service catalog management
- Contact information & location

### 4. **Booking System**
- Blood test booking
- Home sample collection scheduling
- Lab visit bookings
- Booking status tracking
- Appointment notifications

### 5. **Report Management**
- PDF upload & storage
- Report parsing (OCR)
- Parameter extraction
- Abnormal detection
- Report versioning
- Download tracking

### 6. **Health Tracking**
- Weekly follow-ups (mood, stress, diet, exercise)
- Monthly health summaries
- Health metrics (weight, BP, glucose, cholesterol)
- Lifestyle tracking
- Symptom logging

### 7. **AI Chat Doctor**
- Text input processing
- Voice/audio transcription
- Symptom analysis
- Health history analysis
- Condition prediction
- Risk assessment
- Recommendation generation

### 8. **Doctor Dashboard**
- Patient list with abnormal flags
- Trend analysis
- Risk scoring
- Alert generation
- Patient communication

### 9. **ML Systems**
- Symptom classification
- Trend prediction
- Anomaly detection
- Risk scoring
- Condition prediction

### 10. **Multi-language Support**
- Support for: English, Hindi, Gujarati, Tamil, Telugu (configurable)
- Translation layer
- Multilingual NLP
- Voice recognition (multiple languages)

## 🗄️ Database Schema

### Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `app_users` | Patient accounts | id, email, phone, name, age, gender |
| `labs` | Partner labs | id, name, address, contact, services |
| `lab_bookings` | Test bookings | id, user_id, lab_id, status, scheduled_date |
| `reports` | Lab reports | id, user_id, report_date, pdf_url, status |
| `parameters` | Report parameters | id, report_id, name, value, unit, status |
| `weekly_follow_ups` | Weekly health logs | id, user_id, weight, mood, symptoms |
| `monthly_follow_ups` | Monthly summaries | id, user_id, summary, recommendations |
| `chat_sessions` | Chat history | id, user_id, message, response, risk_level |
| `predictions` | ML predictions | id, user_id, condition, confidence, date |
| `health_metrics` | Tracked metrics | id, user_id, metric_name, value, timestamp |
| `doctors` | Doctor accounts | id, name, hospital, speciality, contact |
| `facilities` | Hospitals/clinics | id, name, address, lat, lng, contact |
| `abnormal_alerts` | Risk alerts | id, user_id, alert_type, severity, status |
| `api_keys` | Developer keys | id, user_id, key_hash, rate_limit |

## 🔐 Security Features

1. **Authentication**
   - JWT tokens (HS256)
   - Password hashing (bcrypt)
   - Refresh tokens
   - Session management

2. **Authorization**
   - Role-based access control
   - Resource ownership verification
   - Rate limiting
   - API key validation

3. **Data Protection**
   - SQL injection prevention (ORM)
   - XSS prevention
   - CORS configuration
   - HTTPS enforcement (production)
   - Data encryption at rest (optional)

4. **Compliance**
   - HIPAA-readiness (audit logs, access controls)
   - GDPR-readiness (data retention, deletion)
   - PII protection
   - Consent management

## 📊 API Endpoints

### Authentication
```
POST   /auth/register          # User signup
POST   /auth/login             # User login
POST   /auth/refresh           # Refresh token
GET    /auth/me                # Current user
POST   /auth/logout            # Logout
```

### User Management
```
GET    /users/me               # User profile
PATCH  /users/me               # Update profile
GET    /users/me/health        # Health summary
DELETE /users/me               # Delete account
```

### Labs & Bookings
```
GET    /labs                   # List labs
GET    /labs/{id}              # Lab details
POST   /bookings               # Create booking
GET    /bookings               # My bookings
GET    /bookings/{id}          # Booking details
PATCH  /bookings/{id}/cancel   # Cancel booking
```

### Reports
```
POST   /reports/upload         # Upload PDF
GET    /reports                # My reports
GET    /reports/{id}           # Report details
GET    /reports/{id}/download  # Download PDF
DELETE /reports/{id}           # Delete report
```

### Follow-ups
```
POST   /follow-ups/weekly      # Weekly check-in
GET    /follow-ups/weekly      # Weekly history
POST   /follow-ups/monthly     # Monthly report
GET    /follow-ups/monthly     # Monthly history
```

### Chat Doctor
```
POST   /chat                   # Text message
POST   /chat/voice             # Voice message
GET    /chat/history           # Chat history
```

### Doctor Dashboard
```
GET    /doctor/patients        # High-risk patients
GET    /doctor/patients/{id}   # Patient details
GET    /doctor/reports         # Abnormal reports
GET    /doctor/alerts          # Risk alerts
```

### Nearby Services
```
GET    /nearby/doctors         # Find doctors
GET    /nearby/hospitals       # Find hospitals
GET    /nearby/emergency       # Emergency services
```

### Admin/Developer
```
POST   /developer/signup       # Create dev account
GET    /developer/api-keys     # My API keys
POST   /developer/api-keys     # Generate new key
DELETE /developer/api-keys/{id} # Delete key
```

## 🔄 Data Flow

### Report Upload Flow
```
1. User uploads PDF
2. Store file in uploads/
3. Queue OCR processing (async, Celery)
4. Extract text via OCR
5. Parse parameters (LOINC normalization)
6. Detect abnormal values
7. Run ML predictions
8. Store results in DB
9. Notify user
10. Index for search
```

### Chat Doctor Flow
```
1. User sends message (text or voice)
2. If voice: transcribe to text
3. Extract user ID & language preference
4. Retrieve user's health history (2 months)
5. Analyze symptoms (NLP)
6. Predict conditions (ML)
7. Score risk (0-100)
8. Generate recommendations
9. Store chat in DB
10. Return response + risk_level
11. If high risk: suggest nearby doctors
```

### Weekly Check-in Flow
```
1. User submits weekly form
2. Validate & store in DB
3. Calculate health score
4. Detect anomalies
5. Generate insights
6. If abnormal: create alert
7. Notify doctor (if subscribed)
```

## 🛠️ Technology Stack

**Language:** Python 3.10+  
**Framework:** FastAPI  
**Database:** PostgreSQL (SQLAlchemy async)  
**Auth:** JWT, OAuth2  
**Background Jobs:** Celery + Redis  
**ML:** scikit-learn, XGBoost, transformers  
**NLP:** spaCy, NLTK  
**Voice:** Whisper (OpenAI), SpeechRecognition  
**ORM:** SQLAlchemy 2.0 (async)  
**Validation:** Pydantic v2  
**Testing:** pytest, pytest-asyncio  
**Deployment:** Docker, K8s ready  

## ✅ Implementation Checklist

- [ ] Enhanced models (all 14 tables)
- [ ] Pydantic schemas (request/response)
- [ ] Service layers (business logic)
- [ ] API routers (all endpoints)
- [ ] Authentication & authorization
- [ ] Database migrations
- [ ] ML integration
- [ ] Background tasks (Celery)
- [ ] Error handling & logging
- [ ] Unit tests
- [ ] Integration tests
- [ ] API documentation (OpenAPI)
- [ ] Docker setup
- [ ] CI/CD pipeline

## 🚀 Next Steps

1. Review and approve this architecture
2. Run database migrations
3. Load ML models
4. Implement each module systematically
5. Write tests for each module
6. Deploy to staging environment
7. Performance testing
8. Security audit
9. Deploy to production

---

**Status:** Architecture Ready  
**Version:** 1.0  
**Last Updated:** March 7, 2026
