# Cloud-Based AI Interview and Candidate Assessment Platform

> **Important Architecture Notice:** This is the **LOCAL DEVELOPMENT (Phase 1)** version of the platform. All AWS cloud dependencies (Amazon EC2, S3, RDS, Lambda, SNS, CloudWatch, IAM) have been intentionally replaced with clean local equivalents and service abstractions (`StorageService`, SQLite via SQLAlchemy, synchronous PDF extraction). This allows running and verifying the entire application locally with zero cloud costs or infrastructure prerequisites before migrating components to AWS in Phase 2.

---

## 1. Project Overview

The **Cloud-Based AI Interview and Candidate Assessment Platform** is an intelligent, dual-role hiring system designed for modern engineering teams. It allows recruiters to publish technical job openings with specific skill requirements, enables candidates to upload PDF resumes, and dynamically conducts **adaptive, multi-round technical interviews** powered by external Generative AI (Google Gemini).

Instead of static, repetitive questionnaires, the system evaluates candidate responses in real time, generates tailored follow-up questions based on background and previous answers, and synthesizes an executive candidate assessment scorecard with hiring recommendations.

---

## 2. Features

### Candidate Workflow
- **Secure Authentication**: Candidate registration and JWT-based session management with role isolation.
- **Resume Parsing**: PDF resume upload with automated local text extraction (`pypdf`), stored via the `StorageService` abstraction.
- **Job Discovery**: Browse available technical positions posted by recruiters.
- **Adaptive AI Interview**:
  - Personalized opening question derived from the job requirements and candidate resume context.
  - Multi-round technical interview adapting to candidate responses and performance.
  - Configurable interview length (`INTERVIEW_QUESTION_COUNT`).
  - Instantaneous round feedback (score, correctness, strengths, weaknesses, constructive advice).
- **Comprehensive Scorecard**: Executive assessment report displaying calculated average score, hiring recommendation, technical strengths, weak areas, and question-by-question transcript breakdown.

### Recruiter Workflow
- **Secure Authentication**: Recruiter registration and JWT-based login with role-based route guards.
- **Job Lifecycle Management**: Create, view, update, and delete job postings with specified skill requirements.
- **Candidate Pool Roster**: View all candidates who have interviewed for your job postings, their resume status, interview counts, and highest scores.
- **Candidate Dossier**: View candidate profile, review extracted resume text, and inspect all completed and in-progress interviews.
- **Executive Assessment Reports**: Review candidate scorecards, hiring recommendations (`Strong Hire`, `Hire`, `Consider`, `Do Not Hire`), and detailed answer evaluations.

---

## 3. Architecture

### Local Architecture vs. Future AWS Architecture

```
+-------------------------------------------------------------------------------+
|                             CLIENT / PRESENTATION                             |
|         React 18 + Vite SPA (Candidate & Recruiter Portals, React Router)     |
+-------------------------------------------------------------------------------+
                                      |
                                      | REST API (JWT Authenticated)
                                      v
+-------------------------------------------------------------------------------+
|                            FASTAPI BACKEND CORE                               |
|                                                                               |
|  +---------------------+   +---------------------+   +---------------------+  |
|  |     Auth & JWT      |   |   Job Management    |   |  Interview Engine   |  |
|  +---------------------+   +---------------------+   +---------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  |                           Service Abstractions                          |  |
|  |  * StorageService  ---> LocalStorageService (Local) / S3Storage (AWS)   |  |
|  |  * LLMService      ---> External Generative AI (Gemini / Bedrock)       |  |
|  |  * ResumeService   ---> Local PyPDF (Local) / AWS Lambda (AWS)          |  |
|  |  * AssessmentServ. ---> Synthesizes aggregate scores & executive report |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
           |                                                      |
           v                                                      v
+-----------------------+                              +-----------------------+
|  RELATIONAL DATABASE  |                              |    FILE STORAGE       |
|  * SQLite (Local)     |                              |  * backend/uploads/   |
|  * Amazon RDS (Cloud) |                              |  * Amazon S3 (Cloud)  |
+-----------------------+                              +-----------------------+
```

---

## 4. Technology Stack

### Backend
- **Framework**: Python 3.12, FastAPI
- **ORM / Database**: SQLAlchemy 2.0, SQLite (Local Development)
- **Validation**: Pydantic v2 & `pydantic-settings`
- **Security**: JWT (`PyJWT`), Password Hashing (`bcrypt`)
- **PDF Extraction**: `pypdf`
- **Generative AI**: Google Gemini API (`google-generativeai` / configurable LLM client) with resilient contextual fallbacks

### Frontend
- **Framework**: React 18, Vite
- **Routing**: React Router v6
- **Icons**: Lucide React
- **Styling**: Modern, responsive custom CSS design system

---

## 5. Local Setup & Environment Variables

### Backend Configuration (`backend/.env`)

Copy the example configuration:
```bash
cp backend/.env.example backend/.env
```

Configuration parameters:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./sql_app.db` |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens | Secure random string |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token validity duration | `1440` (24 hours) |
| `LLM_API_KEY` | Google Gemini API key (optional for dev) | `AIzaSy...` |
| `LLM_MODEL` | Gemini model name | `gemini-1.5-flash` |
| `INTERVIEW_QUESTION_COUNT` | Target number of questions per interview | `5` |
| `UPLOAD_DIR` | Directory for storing uploaded resumes | `uploads` |
| `STORAGE_BACKEND` | Storage implementation (`local` or `s3`) | `local` |
| `ALLOWED_ORIGINS` | Permitted CORS origins | `http://localhost:5173,http://127.0.0.1:5173` |

> **Note on LLM API Key**: If `LLM_API_KEY` is not provided or set to the placeholder, the platform uses an intelligent, context-aware fallback engine that derives questions and evaluations from the job requirements and candidate resume, ensuring zero crashes during local testing.

### Frontend Configuration (`frontend/.env`)

Copy the frontend example:
```bash
cp frontend/.env.example frontend/.env
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000/api` |

---

## 6. How to Run Locally

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Node.js 18+ & npm

### Step 1: Set Up and Start Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
uvicorn app.main:app --reload --port 8000
```
The backend will start at: `http://localhost:8000`  
Interactive API Docs (Swagger UI): `http://localhost:8000/docs`

### Step 2: Set Up and Start Frontend

Open a second terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Start Vite development server
npm run dev
```
The frontend will start at: `http://localhost:5173`

---

## 7. Running Backend Automated Tests

The backend test suite runs isolated in-memory SQLite instances and uses a mocked LLM service requiring no external API keys or cloud resources:

```bash
cd backend
.\venv\Scripts\python -m pytest tests -v
```

The automated suite verifies:
- Candidate and Recruiter registration & JWT authentication
- Duplicate email prevention and invalid credential rejections
- Role-based authorization guards (candidates cannot create jobs, recruiters cannot start candidate interviews)
- PDF resume upload and text extraction
- Multi-round adaptive interview workflow, evaluation scoring, and completion
- Recruiter analytics dashboard and candidate roster

---

## 8. API Overview

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Public | Register new candidate or recruiter account |
| `POST` | `/api/auth/login` | Public | Authenticate with email/password and obtain JWT |
| `GET` | `/api/auth/me` | Authenticated | Retrieve current user profile |
| `GET` | `/api/jobs` | Authenticated | List all active job postings |
| `POST` | `/api/jobs` | Recruiter | Create a new job opening |
| `PUT` | `/api/jobs/{id}` | Recruiter | Update job details (owner only) |
| `DELETE` | `/api/jobs/{id}` | Recruiter | Delete job posting (owner only) |
| `POST` | `/api/resumes/upload` | Candidate | Upload PDF resume, extract text, store locally |
| `GET` | `/api/resumes/latest` | Candidate | Retrieve candidate's latest resume |
| `POST` | `/api/interviews` | Candidate | Start interview for a job; generates Question #1 |
| `GET` | `/api/interviews/{id}` | Candidate / Recruiter | Retrieve interview status and question history |
| `POST` | `/api/interviews/{id}/answer` | Candidate | Submit answer; evaluates response and generates follow-up |
| `GET` | `/api/interviews/{id}/results`| Candidate / Recruiter | View final assessment scorecard and breakdown |
| `GET` | `/api/candidates/dashboard` | Candidate | Candidate statistics and recent interviews |
| `GET` | `/api/recruiters/dashboard` | Recruiter | Recruiter overview, jobs, and candidate metrics |
| `GET` | `/api/recruiters/candidates` | Recruiter | List all candidates who interviewed for recruiter's jobs |
| `GET` | `/api/recruiters/candidates/{id}`| Recruiter | View candidate details, resume text, and interview history |

---

## 9. Current Limitations (Local Phase)

1. **Synchronous Resume Processing**: Text extraction runs in-process during upload instead of an asynchronous event-driven queue.
2. **Local Storage**: Files are stored on the local file system under `backend/uploads/` rather than cloud object storage.
3. **Single Instance Database**: SQLite is utilized for zero-configuration local runs rather than a high-availability relational cluster.
4. **Basic Notification Layer**: Recruiter updates are queried directly from the database rather than pushed via SNS or WebSockets.

---

## 10. Future AWS Migration Plan (Phase 2)

The codebase has been designed with strict abstractions to make AWS migration seamless:

1. **Amazon S3 (`S3StorageService`)**:
   - `StorageService` interface in `app/services/storage_service.py` is ready to swap `LocalStorageService` with `boto3`-backed S3 operations (`s3.upload_fileobj`, `generate_presigned_url`).
2. **Amazon RDS (PostgreSQL)**:
   - Update `DATABASE_URL` from `sqlite:///` to `postgresql+asyncpg://` or `postgresql://`. All SQLAlchemy models and relationships use standard ANSI SQL conventions.
3. **AWS Lambda (`resume_processor`)**:
   - Move PDF parsing to an S3 event-driven Lambda function (see `lambda/resume_processor/README.md`) using Amazon SQS for background processing.
4. **Amazon EC2 / ECS Fargate**:
   - Containerize the FastAPI backend via Docker and deploy on Amazon EC2 / ECS behind an Application Load Balancer (ALB).
5. **Amazon SNS / SES**:
   - Dispatch candidate completion events to recruiters via Amazon SNS topics or email notifications via Amazon SES.
6. **Amazon CloudWatch**:
   - Stream structured Uvicorn application logs and capture custom performance metrics in CloudWatch Logs.
7. **AWS IAM**:
   - Attach IAM instance profiles to EC2/Lambda for least-privilege access without hardcoding AWS access keys.

---

## 11. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
