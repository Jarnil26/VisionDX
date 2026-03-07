# VisionDX – Full Project Documentation

**Health Monitoring & Medical Lab Collaboration Platform**

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Lab Collaboration](#2-lab-collaboration)
3. [Weekly Follow-Up](#3-weekly-follow-up)
4. [Monthly Follow-Up](#4-monthly-follow-up)
5. [Reports in the App & Download](#5-reports-in-the-app--download)
6. [ML Chat Doctor (Text + Voice)](#6-ml-chat-doctor-text--voice)
7. [Nearby Doctor/Hospital by Condition](#7-nearby-doctorhospital-by-condition)
8. [Doctor Dashboard & Abnormal Data](#8-doctor-dashboard--abnormal-data)
9. [Multilingual Support](#9-multilingual-support)
10. [System Architecture](#10-system-architecture)
11. [API Reference Summary](#11-api-reference-summary)
12. [Technology Stack](#12-technology-stack)
13. [Security & Privacy](#13-security--privacy)

---

## 1. Project Overview

**VisionDX** is a digital health companion that connects users with partner labs and provides AI-driven health insights. Users can:

- **Upload pre-reports** (past lab reports in PDF) and **book home sample collection** with partner labs.
- Complete **weekly** (once per week) and **monthly** (detailed) follow-ups for ongoing tracking.
- Receive **lab reports digitally** in the app when a home-collected sample is processed—and **download** them anytime.
- Use an **ML Chat Doctor** (text or voice): describe symptoms; the system uses **previous 2 months** of data to **predict possible conditions** (e.g. stomach ache + junk food → possible infection or digestive issue). If something serious is detected, the app suggests **nearby doctors/hospitals** relevant to that condition.
- **Doctors** get a dashboard where **abnormal data is highlighted** and ML helps prioritize and predict.

The platform is designed to **support all languages** (API and UI) for global use.

---

## 2. Lab Collaboration

### 2.1 What Users Can Do

| Feature | Description |
|--------|-------------|
| **Upload pre-report** | User uploads existing lab report PDFs. These are processed (OCR, parsing, abnormal detection, ML) and stored under their account. |
| **Book home sample collection** | User selects a partner lab and books a test with **home sample collection** or **lab visit**. They choose test type and preferred date/time. |
| **Receive report in app** | When the lab completes the test and uploads the report via the Lab API, the report is **linked to the user’s booking** and appears in **their app**. |
| **Download report** | User can **download** the report PDF from the app anytime (e.g. via report ID or “My Reports”). |

### 2.2 Lab Partner Integration

- Partner labs integrate with the VisionDX backend.
- **Lab API** (authenticated with `X-Lab-API-Key`):
  - **Submit report**: Lab uploads the report PDF; optionally links it to a **booking ID**. The system then links the report to the user and marks the booking as “report_ready.”
  - **Update booking status**: e.g. `scheduled` → `sample_collected` → `processing` → `report_ready`.

### 2.3 User Flow (Summary)

1. User signs up / logs in.
2. User **uploads** any previous reports (PDF).
3. User **books** a test (home sample or lab visit) with a partner lab.
4. Lab collects sample (for home: phlebotomist visits); lab updates status.
5. Lab uploads the report via Lab API (with optional `booking_id`).
6. Report appears in the **user’s app** and can be **downloaded**.

---

## 3. Weekly Follow-Up

**Once per week**, the user completes a short follow-up so the system can track behaviour and symptoms over time (and use this in the ML Chat Doctor).

### 3.1 Data Collected (Weekly)

| Field | Description |
|-------|-------------|
| **Week start date** | Start of the week (e.g. Monday). |
| **Weight** | Current weight (e.g. in kg). |
| **Mood / mental state** | How they felt during the week: e.g. **sad**, **anxious**, **mentally depressed**, **stressed**, **calm**, **happy**. |
| **Physical symptoms** | e.g. **pain** (location/severity), **fatigue**, **headache**, **digestive issues**, **sleep problems**. |
| **Diet & lifestyle** | Brief note on diet (e.g. fast food, junk food, balanced) and lifestyle (exercise, sleep, alcohol, etc.). |
| **Notes** | Any other observations (e.g. “ate junk for 2 weeks”, “low energy”). |

This gives a **proper weekly behaviour snapshot** (mood, pain, mental state, lifestyle) that is used later in the **2‑month ML analysis** for the Chat Doctor.

### 3.2 API

- **POST /follow-ups/weekly** – Submit one weekly follow-up (auth: user token).
- **GET /follow-ups/weekly** – List user’s weekly follow-ups (optional `from` / `to`).

---

## 4. Monthly Follow-Up

**Once per month**, the user (or system) completes a **full, detailed** follow-up.

### 4.1 Data Collected (Monthly)

| Field | Description |
|-------|-------------|
| **Month start** | First day of the month. |
| **Summary** | Overall health summary for the month. |
| **Health trends** | Progress or decline (e.g. weight trend, energy trend). |
| **Recommendations** | Suggested lifestyle or next steps. |
| **Medical alerts** | Any flags from the system or user (e.g. “follow up with doctor”). |

This feeds into **trend analysis** and the **ML Chat Doctor** when aggregating the last 2 months.

### 4.2 API

- **POST /follow-ups/monthly** – Submit monthly follow-up.
- **GET /follow-ups/monthly** – List user’s monthly follow-ups.

---

## 5. Reports in the App & Download

- **My reports**: **GET /users/me/reports** returns all reports linked to the logged-in user (including those from home sample bookings when the lab uploads with `booking_id`).
- **Download**: Each report has a `report_id`. The app can **download** the PDF via the backend endpoint that serves the file (e.g. **GET /pdf/{report_id}** or equivalent).
- When a **home sample** is processed and the lab submits the report with the booking ID, that report is automatically linked to the user and appears in “My Reports” and is **downloadable** in the app.

---

## 6. ML Chat Doctor (Text + Voice)

### 6.1 Purpose

Users describe how they feel (e.g. “stomach ache for 2 weeks, I regularly eat fast and junk food”). The system:

- Uses **past 2 months** of data: **reports** (lab parameters), **weekly follow-ups** (mood, pain, diet, symptoms), **monthly follow-ups**.
- Runs **ML models** to **predict possible conditions** (e.g. infection, digestive disorder, lifestyle-related issues).
- Suggests **next steps** (lifestyle changes, lab test, see a doctor).
- If a **serious condition** is detected (or emergency keywords), it triggers **emergency alert** and **nearby doctors/hospitals** (optionally by **condition/specialty**).

### 6.2 Input: Text and Voice

| Input type | How it works |
|------------|----------------|
| **Text** | User types the message (e.g. “Stomach ache for 2 weeks, eating mostly fast/junk food”). |
| **Voice** | User records **audio** (e.g. speech). The app sends the audio to the backend; backend converts **speech-to-text** (transcription), then runs the **same ML flow** as for text. Response can be text (and optionally text-to-speech on the client). |

So the **same ML logic** runs for both text and voice; voice is just “voice → text → existing chat pipeline.”

### 6.3 Example

- **User (text or voice):** “I have stomach ache for 2 weeks and I’ve been eating a lot of fast and junk food.”
- **System:**  
  - Aggregates last 2 months (reports + weekly/monthly follow-ups).  
  - ML predicts e.g. **possible infection or digestive disorder**.  
  - Suggests: lab test (e.g. stool/culture) or **nearby gastroenterologist**.  
  - If critical: **emergency alert** + **nearby hospitals/doctors**.

### 6.4 API

- **POST /chat** – Send **text** message; get reply, suggestions, emergency flag, nearby facilities (and optionally by predicted condition).
- **POST /chat/voice** – Send **audio** file; backend transcribes → runs same logic as **POST /chat** → returns same structure (reply, suggestions, emergency, nearby facilities). Supports **all languages** (transcription and analysis).

---

## 7. Nearby Doctor/Hospital by Condition

- When the ML Chat Doctor predicts a **condition** (e.g. digestive, cardiac, mental health), the “nearby facilities” list can be **filtered by specialty** (e.g. gastroenterologist, cardiologist, psychiatrist).
- In **emergency** mode, the list includes **hospitals / emergency care**.
- Backend can:
  - Use a **mapping**: predicted condition → specialty (e.g. “Digestive disorder” → “Gastroenterologist”).
  - Return **nearby doctors/hospitals** for that specialty (via internal DB or external API like Google Places / healthcare providers).  
- This ensures that when someone has e.g. stomach issues, they see **relevant** doctors (e.g. gastroenterologist), not only generic emergency list.

---

## 8. Doctor Dashboard & Abnormal Data

For **doctors** (or clinic staff):

- **Abnormal reports**: List of reports where at least one parameter is **abnormal** (LOW/HIGH). Sorted e.g. by **number of abnormal parameters** (prioritization).
- **Per-report view**: Full report with **abnormal values highlighted**, AI predictions, and PDF link.
- **ML support**: Predictions and highlights help in **early detection** and **proactive care**.

### API

- **GET /doctor/abnormal-reports** – List reports with abnormal data (prioritized).
- **GET /doctor/report/{report_id}** – Full report (patient, parameters, predictions, summary, PDF URL).

---

## 9. Multilingual Support

- **All languages** are supported in the sense that:
  - **Input**: User can send **text** or **voice** in **any language**.  
  - **Voice**: Speech-to-text can be configured for multiple languages (e.g. via language hint or auto-detect).  
  - **Output**: API can return replies and suggestions in a **requested language** (e.g. via `Accept-Language` header or `lang` query/body parameter).  
- Design:
  - Backend accepts **language** (e.g. `lang=en` or `Accept-Language: hi`).
  - Where applicable (e.g. chat reply, suggestions), responses are **localized** (e.g. with a translation layer or multilingual templates).  
- This applies to: **Chat Doctor** (text + voice), **follow-up labels**, and **doctor-facing** content where needed.

---

## 10. System Architecture

```text
┌─────────────┐     ┌──────────────────────────────────────────────────┐     ┌─────────────┐
│  User App   │────▶│  Backend API (VisionDX)                          │────▶│  Labs       │
│  (Mobile/  │     │  • Auth (users/labs)                              │     │  (Lab API   │
│   Web)     │     │  • Pre-report upload / My reports / Download      │     │   report    │
│            │     │  • Lab bookings (home sample / lab visit)         │     │   submit)   │
│            │     │  • Weekly & monthly follow-ups                    │     └─────────────┘
│            │     │  • ML Chat (text + voice → transcript → ML)       │
│            │     │  • Nearby facilities (by condition + emergency)    │
│            │     │  • Doctor dashboard (abnormal reports, highlights) │
│            │     │  • Multilingual (lang param / Accept-Language)    │
│            │     └─────────────────────┬────────────────────────────┘
│            │                             │
│            │                             ▼
│            │     ┌──────────────────────────────────────────────────┐
│            │     │  Database + ML Engine                            │
│            │     │  • Users, Reports, Parameters, Predictions        │
│            │     │  • Weekly / Monthly follow-ups, Chat sessions     │
│            │     │  • Labs, Bookings, Facilities (by specialty)     │
│            │     └──────────────────────────────────────────────────┘
└─────────────┘
```

---

## 11. API Reference Summary

| Area | Method | Endpoint | Auth | Description |
|------|--------|----------|------|-------------|
| **App user** | POST | /users/register | - | Register (email or phone + profile) |
| | POST | /users/login | - | Login → JWT |
| | GET  | /users/me | User | Profile |
| | PATCH| /users/me | User | Update profile |
| | GET  | /users/me/reports | User | My reports |
| | POST | /users/me/reports/upload | User | Upload pre-report PDF |
| **Labs (user)** | GET  | /labs | User | List partner labs |
| | GET  | /labs/bookings | User | My bookings |
| | POST | /labs/bookings | User | Create booking (home/lab visit) |
| **Lab API** | PUT  | /lab-api/bookings/{id}/status | Lab key | Update booking status |
| | POST | /lab-api/reports | Lab key | Submit report PDF (optional booking_id) |
| **Follow-ups** | POST | /follow-ups/weekly | User | Submit weekly (weight, mood, pain, symptoms, diet) |
| | GET  | /follow-ups/weekly | User | List weekly |
| | POST | /follow-ups/monthly | User | Submit monthly (detailed) |
| | GET  | /follow-ups/monthly | User | List monthly |
| **Chat Doctor** | POST | /chat | User | Text message → reply, suggestions, emergency, facilities |
| | POST | /chat/voice | User | Audio → transcript → same as /chat (supports all languages) |
| **Report download** | GET  | /pdf/{report_id} | - | Download report PDF |
| **Doctor** | GET  | /doctor/abnormal-reports | - | List reports with abnormal data |
| | GET  | /doctor/report/{report_id} | - | Full report + PDF URL |

**Multilingual**: Use `Accept-Language` or `lang` (query/body) where supported (e.g. `/chat`, `/chat/voice`).

---

## 12. Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy (async), Pydantic.
- **Database**: SQLite (dev) / PostgreSQL (prod).
- **ML**: Disease prediction (e.g. XGBoost + rule engine + knowledge base), abnormal detection, risk scoring.
- **OCR**: For PDF report parsing (e.g. Tesseract, pdfplumber).
- **Voice**: Speech-to-text (e.g. Whisper or cloud STT) for `/chat/voice`; supports multiple languages.
- **Optional**: Translation API or multilingual templates for responses.

---

## 13. Security & Privacy

- **Auth**: JWT for app users; API key for labs; role-based for doctors.
- **Data**: Reports and follow-ups are scoped to the authenticated user; doctors see only what is allowed (e.g. abnormal reports, no raw PII beyond need).
- **Voice**: Audio can be processed server-side and not stored long-term if not required; transcripts follow same privacy as chat.
- **Multilingual**: No extra PII exposure; language is a display/preference only.

---

---

## Implementation Status (Backend)

| Feature | Status | Notes |
|--------|--------|--------|
| Lab collaboration (pre-report upload, home sample booking) | Done | POST /users/me/reports/upload, POST /labs/bookings, Lab API |
| Report in app + download | Done | GET /users/me/reports, GET /pdf/{report_id} |
| Weekly follow-up (weight, mood, mental state, pain, symptoms, diet) | Done | mental_state, pain_level, pain_notes added |
| Monthly follow-up (detailed) | Done | POST/GET /follow-ups/monthly |
| ML Chat (text) + 2-month data | Done | POST /chat, uses reports + weekly/monthly |
| ML Chat (voice) | Done | POST /chat/voice; install SpeechRecognition for STT (all languages) |
| Nearby facilities by condition | Done | Suggestions include specialty (e.g. Gastroenterologist for stomach) |
| Doctor dashboard (abnormal highlight) | Done | GET /doctor/abnormal-reports, GET /doctor/report/{id} |
| Multilingual (lang param) | Done | body.lang, Accept-Language, X-Lang for voice; reply i18n can be added |

*This document describes the **full VisionDX project**: lab collaboration (pre-report upload, home sample booking, report in app + download), weekly/monthly follow-ups, ML Chat Doctor (text + voice), nearby doctor/hospital by condition, doctor dashboard with abnormal data, and multilingual support.*
