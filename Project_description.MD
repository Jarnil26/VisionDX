# VisionDX — The Comprehensive AI-Powered Medical Intelligence Platform

VisionDX is a next-generation healthcare ecosystem designed to bridge the gap between complex medical diagnostics and patient-centric healthcare. By leveraging advanced Machine Learning (ML), Natural Language Processing (NLP), and a modern web architecture, VisionDX provides a seamless experience for patients, doctors, labs, and developers alike.

---

## 📑 Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Project Philosophy & Vision](#2-project-philosophy--vision)
3. [Core Platform Features](#3-core-platform-features)
   - [3.1 Patient Experience](#31-patient-experience)
   - [3.2 Doctor Surveillance Hub](#32-doctor-surveillance-hub)
   - [3.3 Lab Collaboration System](#33-lab-collaboration-system)
   - [3.4 Developer Portal](#34-developer-portal)
4. [AI Chat Doctor V2: The Intelligence Engine](#4-ai-chat-doctor-v2-the-intelligence-engine)
   - [4.1 Multilingual NLP Pipeline](#41-multilingual-nlp-pipeline)
   - [4.2 2-Month Contextual Analysis](#42-2-month-contextual-analysis)
   - [4.3 Rule-Based Symptom Analyzer](#43-rule-based-symptom-analyzer)
   - [4.4 Emergency Detection & Global Triage](#44-emergency-detection--global-triage)
5. [Medical Analysis & Machine Learning](#5-medical-analysis--machine-learning)
   - [5.1 PDF Report Ingestion & OCR](#51-pdf-report-ingestion--ocr)
   - [5.2 Biomarker Extraction & LOINC Normalization](#52-biomarker-extraction--loinc-normalization)
   - [5.3 Disease Prediction ML Engine](#53-disease-prediction-ml-engine)
   - [5.4 Risk Scoring & Anomaly Detection](#54-risk-scoring--anomaly-detection)
6. [System Architecture](#6-system-architecture)
   - [6.1 High-Level Overview](#61-high-level-overview)
   - [6.2 Backend (FastAPI Architecture)](#62-backend-fastapi-architecture)
   - [6.3 Frontend (Next.js 14 & App Router)](#63-frontend-nextjs-14--app-router)
   - [6.4 Database Schema & Scalability](#64-database-schema--scalability)
7. [Technical Stack Deep Dive](#7-technical-stack-deep-dive)
8. [API Reference (Comprehensive)](#8-api-reference-comprehensive)
9. [Development & Deployment Guide](#9-development--deployment-guide)
10. [Security, Privacy & HIPAA Readiness](#10-security-privacy--hipaa-readiness)
11. [Conclusion & Future Roadmap](#11-conclusion--future-roadmap)

---

## 1. Executive Summary
VisionDX is not just a portal; it is an intelligent health companion. In an era where medical data is fragmented and often incomprehensible to the average patient, VisionDX uses AI to translate raw biomarker data into actionable insights. It serves as a centralized hub where lab results, lifestyle habits, and AI-driven triage converge to provide a holistic view of human health.

## 2. Project Philosophy & Vision
The core philosophy of VisionDX is "Proactive, not Reactive." We believe that early detection and continuous monitoring are the keys to long-term wellness. By analyzing behavioral data (weekly follow-ups) alongside clinical data (blood reports), VisionDX can detect subtle shifts in health before they become critical issues. Our vision is to democratize expert medical knowledge using AI, making it accessible even in resource-constrained or remote areas.

---

## 3. Core Platform Features

### 3.1 Patient Experience
The patient portal is designed for simplicity and trust. It empowers users to take control of their medical journey through:
- **Biometric History**: A centralized view of all historical lab results.
- **Health Trend Visualization**: Graphical representations of weight, vitals, and biomarker changes over time.
- **Weekly Behavior Logs**: A specialized "check-in" system where patients record mood, stress levels, digestive habits, and physical pain. This data allows the AI to understand "why" a report might show abnormal values (e.g., high glucose due to a week of 'junk food' behavior).
- **Home Sample Booking**: Direct integration with partner labs allows patients to book phlebotomy visits to their homes, with results delivered directly into the VisionDX app.

### 3.2 Doctor Surveillance Hub
The Doctor Dashboard moves beyond static lists. It features:
- **Automated Triage**: Patients are automatically ranked by "Risk Score" based on ML predictions.
- **Abnormal Highlight System**: Every report is scanned for values outside reference ranges (LOW/HIGH), which are then color-coded for instant clinical review.
- **Proactive Alerts**: Doctors see emerging health threats (e.g., rising creatinine levels over 3 reports) before a clinical "cut-off" is reached.

### 3.3 Lab Collaboration System
Labs are the "data providers" of the ecosystem. VisionDX provides labs with:
- **X-Lab-API-Key Access**: Secure, high-throughput endpoints for pushing report PDFs and biomarker data.
- **Booking Management**: A workflow to accept, schedule, and mark home-collection bookings as "Report Ready."
- **Digital Delivery**: Automated linking of reports to patient accounts using internal `booking_id` mapping.

### 3.4 Developer Portal
VisionDX is built to be an open platform. Developers can:
- **Register for API access** to utilize VisionDX’s prediction engine in their own health apps.
- **Manage API Keys**: Secure generation and rotation of keys.
- **Documentation access**: Live Swagger/OpenAPI docs for rapid integration.

---

## 4. AI Chat Doctor V2: The Intelligence Engine

The "AI Chat Doctor" is the most advanced component of VisionDX. It is a hybrid system that combines rule-based precision with ML-driven predictions.

### 4.1 Multilingual NLP Pipeline
To support a global user base, the chat system uses a sophisticated NLP pipeline:
1. **Input Detection**: Automatically identifies if the user is typing in English, Hindi, Hinglish, or other regional dialects.
2. **Translation Service**: Translates non-English queries into "AI-English" for the processing engine.
3. **Fuzzy Spelling Correction**: Handles common medical misspellings (e.g., "dibetes" → "diabetes") to ensure keyword matching remains accurate.
4. **Context-Aware Response**: Translates the AI's complex medical advice back into the user's native tongue.

### 4.2 2-Month Contextual Analysis
Unlike "one-shot" AI bots, the AI Chat Doctor looks into the user's past:
- **Recent Reports**: Analyzes blood parameters from the last 60 days.
- **Follow-up Logs**: Checks the last 8 weekly check-ins for lifestyle patterns (e.g., "has been stressed and eating junk for 3 weeks").
- **Aggregated History**: Combines these data points into a single "Health Vector" that informs the ML model.

### 4.3 Rule-Based Symptom Analyzer
We recognize that lab data isn't always available. For immediate advice, the AI uses a 400+ keyword rule set:
- **Postural Back Pain**: Detects "laptop use" + "back pain" to give ergonomic advice.
- **Eye Strain**: Detects "screen time" + "headache" to suggest the 20-20-20 rule.
- **Lifestyle Fatigue**: Detects "no energy" + "stress" to suggest iron/vitamin D checks.
- **Premium Formatting**: Responses are formatted with Markdown (Headers, Emojis, Bullet Points) to ensure they are readable on mobile screens.

### 4.4 Emergency Detection & Global Triage
The system scans every message for "Emergency Keywords" (e.g., chest pain, difficulty breathing, sudden numbness).
- **Crisis Mode**: Instantly halts normal chat and displays a prominent **Red Emergency Banner**.
- **Hospital Routing**: Uses the user's location (or predefined facility database) to show the three nearest emergency rooms.
- **Specialty Mapping**: If a condition like "diabetes" is predicted, it specifically suggests a **Gastroenterologist** or **Endocrinologist**, rather than just a general physician.

---

## 5. Medical Analysis & Machine Learning

VisionDX's "brain" is a collection of ML models and heuristic engines located in the `visiondx/ml` and `visiondx/services` directories.

### 5.1 PDF Report Ingestion & OCR
When a PDF is uploaded via `POST /users/me/reports/upload`:
1. The file is saved to a secure disk storage.
2. An asynchronous process (Celery-ready) begins PDF parsing.
3. Optical Character Recognition (OCR) extracts raw text from the document, preserving spatial relationships.

### 5.2 Biomarker Extraction & LOINC Normalization
Extracting text is only the first step. VisionDX must understand it:
- **Regex Mapping**: Scans for 500+ common biomarker names (e.g., Hemoglobin, HbA1c, TSH).
- **LOINC Standard**: Normalizes varying lab names (e.g., "HBG" and "HGB") into a single standard biomarker ID.
- **Value Parsing**: Extracts numerical values and units (mg/dL, mmol/L) to allow for mathematical comparison.

### 5.3 Disease Prediction ML Engine
The engine uses an ensemble approach (`visiondx/ml/predictor.py`):
- **Feature Engineering**: Converts a list of parameters into a numerical vector.
- **Multiple Models**: Includes pre-trained predictors for:
  - **Diabetes/Glucose Disorders**
  - **Anemia & Iron Deficiencies**
  - **Kidney Function & Creatinine levels**
  - **Thyroid Anomalies**
- **Confidence Scoring**: Every prediction comes with a percentage (e.g., "85% confidence") based on the proximity of values to the training set.

### 5.4 Risk Scoring & Anomaly Detection
Beyond specific diseases, VisionDX calculates a "Global Risk Score" (0-100):
- **Anomaly Detection**: Scans for "fast-moving" biomarkers (e.g., a sudden drop in platelets) that could indicate acute issues.
- **Trend Analysis**: Uses a time-series model to predict where a biomarker will be in 3 months if current lifestyle habits (from follow-ups) continue.

---

## 6. System Architecture

VisionDX is built on a loosely coupled, service-oriented architecture designed for high availability and easy scaling. 

### 6.1 High-Level Overview
The system follows a modern "Frontend-Backend-Service" pattern:
1. **Frontend**: A Next.js 14 Single-Page Application (SPA) serving as the main entry point for all user roles.
2. **API Layer**: A high-performance FastAPI back-end that manages authentication, validation, and request routing.
3. **Intelligence Services**: A suite of specialized Python services (Chat, Report Processing, Prediction) that perform the heavy computational lifting.
4. **Data Persistence**: A relational PostgreSQL/SQLite database that stores structured medical records, user profiles, and ML results.
5. **Static Storage**: A secure file system storage for raw report PDFs and voice audio logs.

### 6.2 Backend (FastAPI Architecture)
The backend (`visiondx/`) is organized into clean domains:
- **`visiondx.api.routes`**: Defines the RESTful API contract. Each route (e.g., `reports.py`, `chat.py`) is decoupled from business logic.
- **`visiondx.services`**: The "Business Core." This is where the actual logic for aggregating health data, managing lab bookings, and generating chat responses resides.
- **`visiondx.database.models`**: Defines the ORM (SQLAlchemy) layer. We use Pydantic schemas (`schemas.py`) to ensure strict data validation at every API boundary.
- **`visiondx.core`**: Contains global dependencies, custom medical exceptions, and the security middleware (JWT/Role-based checks).

### 6.3 Frontend (Next.js 14 & App Router)
The frontend (`frontend/src/app/`) leverages the latest React features:
- **App Router Architecture**: Enables server-side rendering (SSR) for initial page loads while maintaining client-side interactivity for the Chat and Dashboards.
- **Role-Based Layouts**: The `layout.tsx` detects the user's role (Patient, Doctor, Lab, Developer) and dynamically injects the correct navigation bar and sidebar theme.
- **Zustand State Management**: A lightweight, performant store handles authentication tokens and user preferences across the entire session.
- **Premium Component Library**: A tailored collection of UI elements built with Radix UI (ShadCN) ensures a consistent, high-end medical aesthetic.

### 6.4 Database Schema & Scalability
The database is structured for complex relational queries:
- **`AppUser` Table**: Stores patient profile data, age, gender, and encrypted password.
- **`Report` & `Parameter` Tables**: A one-to-many relationship allowing a single PDF to contain hundreds of extracted biomarkers.
- **`WeeklyFollowUp` Table**: Time-stamped logs of lifestyle behaviors.
- **`Laboratory` Table**: Stores partner lab credentials, locations, and API keys.
- **Indexing**: All high-traffic fields (User IDs, Report IDs, API Keys) are indexed to ensure sub-100ms response times.

---

## 7. Technical Stack Deep Dive

VisionDX uses a carefully curated stack to ensure speed, security, and developer productivity.

### 7.1 Backend: The Python Powerhouse
- **FastAPI**: Used for its speed (benchmarking close to Go/Node.js) and automatic OpenAPI (Swagger) documentation.
- **SQLAlchemy (Async)**: Enables non-blocking database queries, crucial for high-concurrency medical portals.
- **Pydantic V2**: Handles high-performance data serialization and robust validation for incoming medical data.
- **PyJWT**: Powers our secure Authentication & Authorization system with token rotation.
- **OCR Engine**: Utilizes Python wrappers for extraction of tabular data from report PDFs.

### 7.2 Frontend: Modern Web Excellence
- **Next.js 14**: Chosen for its built-in SEO optimization and blazing-fast performance.
- **TailwindCSS**: Used for our "Medical-Premium" design system, enabling responsive, pixel-perfect layouts without bloating the CSS.
- **Lucide React**: A comprehensive medical icon set used throughout the dashboard.
- **Axios**: Configured with custom interceptors to handle token expiration and automatic re-authentication.
- **Framer Motion**: Powering our "wow" factor—smooth chat animations and dashboard entrance transitions.

### 7.3 Data & Intelligence Stack
- **Biomarker Knowledge Base**: A proprietary dataset used to map lab names to standardized medical IDs.
- **SpeechRecognition**: High-fidelity STT for voice input, capable of understanding multiple languages and medical terminology.
- **Celery & Redis (Ready)**: The architecture is pre-configured to offload heavy OCR tasks to background workers, ensuring the main API remains responsive.

---

## 8. API Reference (Comprehensive)

VisionDX exposes a RESTful API organized by functional domains. All endpoints (unless noted) require a Bearer JWT in the `Authorization` header.

### 8.1 Authentication & Profile
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/users/register` | Register a new patient account. |
| `POST` | `/users/login` | Authenticate and receive an access token. |
| `POST` | `/users/refresh` | Refresh an expired session token. |
| `GET` | `/users/me` | Fetch the authenticated user's profile. |
| `PATCH` | `/users/me` | Update age, gender, or medical history. |

### 8.2 Medical Laboratory Collaboration
Home sample collection and lab-direct reports are managed here:
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/labs` | List all certified partner laboratories. |
| `POST` | `/labs/bookings` | Schedule a home sample collection or lab visit. |
| `GET` | `/labs/bookings` | View history of pending and completed bookings. |
| `PUT` | `/lab-api/bookings/{id}` | (Lab Only) Update booking status (e.g., "Sample Collected"). |

### 8.3 Medical Report Management
Handle the ingestion and retrieval of clinical data:
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/users/me/reports/upload` | Upload a PDF report for AI processing. |
| `GET` | `/users/me/reports` | Retrieve a list of all processed health reports. |
| `GET` | `/reports/{id}` | Get structured biomarker data for a specific report. |
| `GET` | `/pdf/{report_id}` | Generate a temporary link to download the original PDF. |

### 8.4 Health Tracking (Follow-ups)
Continuous monitoring through behavioral logs:
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/follow-ups/weekly` | Weekly log of mood, weight, and physical symptoms. |
| `GET` | `/follow-ups/weekly` | Retrieve historical weekly behavioral trends. |
| `POST` | `/follow-ups/monthly` | Detailed monthly health self-assessment. |
| `GET` | `/follow-ups/monthly` | View monthly prognosis and recommendations history. |

### 8.5 AI Chat Doctor (Intelligence)
Interactive medical triaging and analysis:
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/chat` | Submit symptoms; receive AI analysis and emergency flags. |
| `POST` | `/chat/voice` | Submit audio; receive transcribed AI analysis and triage. |
| `GET` | `/chat/history` | View historical interactions with the AI Consultant. |

### 8.6 Clinical (Doctor) Dashboard
Restricted endpoints for medical professionals:
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/doctor/patients` | Retrieve list of patients sorted by Risk Score. |
| `GET` | `/doctor/abnormal-reports` | View all reports containing out-of-range biomarkers. |
| `POST` | `/doctor/alerts` | Create a medical intervention alert for a patient. |

---

## 9. Development & Deployment Guide

VisionDX is designed for rapid local development and scalable cloud deployment.

### 9.1 Local Development Prerequisites
- **Python 3.10+**: Core backend runtime.
- **Node.js 18+**: Frontend development environment.
- **Tesseract OCR**: Required for PDF biomarker extraction.
- **Git**: For version control.

### 9.2 Initial Backend Setup
1. **Clone and Virtual Env**:
   ```bash
   git clone [repository_url]
   python -m venv .venv
   source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
   ```
2. **Installation**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configuration**:
   Copy `.env.example` to `.env` and configure your `SECRET_KEY` and `DATABASE_URL`.
4. **Launch**:
   ```bash
   python -m uvicorn visiondx.main:app --port 8000 --reload
   ```

### 9.3 Initial Frontend Setup
1. **Directory Change**:
   ```bash
   cd frontend
   ```
2. **Install Dependencies**:
   ```bash
   npm install
   ```
3. **Environment Sync**:
   Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in your `.env.local`.
4. **Launch Dev Server**:
   ```bash
   npm run dev
   ```

### 9.4 Production Deployment (Render/Docker)
VisionDX is fully containerized. A `Dockerfile` and `docker-compose.yml` are provided in the root to orchestrate the API and PostgreSQL instances. For one-click deployments, use the `render.yaml` template included in the repo.

---

## 10. Security, Privacy & HIPAA Readiness

Security is baked into the DNA of VisionDX. We recognize the sensitivity of medical data and have implemented multiple layers of protection.

### 10.1 Authentication Architecture
- **JWT with HS256**: All user sessions are secured using JSON Web Tokens.
- **Refresh Token Rotation**: Minimizes the risk of session hijacking by requiring frequent token updates.
- **Bcrypt Hashing**: All passwords and API keys are stored as non-reversible hashes using industry-standard salts.

### 10.2 HIPAA & Clinical Compliance
While primarily a tech platform, VisionDX is built with HIPAA principles in mind:
- **Audit Logging**: Every access to a medical report is logged with a timestamp and user ID.
- **Role-Based Access (RBAC)**: Only "Doctors" can see patient registries, and "Labs" can only see bookings assigned to their specific lab ID.
- **PHI Masking**: Patients can choose to share their data with doctors; otherwise, reports remain encrypted and accessible only to the owner.
- **Data Deletion**: Fully supports "Right to be Forgotten" requests, permanently purging data from primary storage and backups.

### 10.3 Infrastructure Security
- **CORS Policies**: Strict Cross-Origin Resource Sharing ensures that only authorized frontend domains can interact with the API.
- **SQL Injection Prevention**: All database interactions utilize SQLAlchemy ORM with prepared statements, eliminating the risk of raw SQL injection attacks.
- **HTTPS Enforcement**: Production environments are configured to reject any non-SSL/TLS traffic.

---

## 11. Conclusion & Future Roadmap

VisionDX 1.0 represents a foundational shift in medical data accessibility. By empowering patients with AI intelligence and providing doctors with predictive triage, we are moving towards a more efficient, accurate, and proactive healthcare system.

### 11.1 The Roadmap Ahead
Our vision for VisionDX 2.0 includes:
- **Real-Time Integration with Wearables**: Syncing with Apple Health and Google Fit for 24/7 vitals tracking.
- **Federated ML Models**: Improving prediction accuracy through decentralized learning while maintaining data privacy.
- **Blockchain for Health Records**: Exploring immutable, patient-owned ledger entries for lab results.
- **Telemedicine Integration**: One-click video consultations directly from the AI Chat Dr interface.

### 11.2 A Final Word
Technology should never replace a doctor, but it can certainly make the doctor's job easier and the patient's journey clearer. VisionDX is committed to being that bridge.

---

**Project Owner:** Jarnil26  
**Project Status:** Production-Ready  
**Documentation Version:** 1.0.4  
**Last Major Audit:** March 7, 2026

*© 2026 VisionDX. All rights reserved.*
