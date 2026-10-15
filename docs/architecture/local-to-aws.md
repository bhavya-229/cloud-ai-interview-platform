# Local-to-AWS Migration Architecture

## Current Local Architecture vs Target AWS Architecture

| Architectural Area | Local Implementation (Current Phase) | Target AWS Service (Cloud Phase) | Migration Path / Strategy |
| :--- | :--- | :--- | :--- |
| **Backend Compute** | Local Uvicorn / FastAPI server | **Amazon EC2** / ECS Fargate | Containerize via Dockerfile; deploy behind Application Load Balancer (ALB). |
| **Relational Database** | Local **SQLite** via SQLAlchemy ORM | **Amazon RDS** (PostgreSQL / Aurora) | Update `DATABASE_URL` from `sqlite:///` to `postgresql://` in environment variables. Run Alembic migrations. |
| **Resume & File Storage**| `LocalStorageService` (`backend/uploads/`) | **Amazon S3** (`S3StorageService`) | Implement `StorageService` interface with `boto3` client against S3 bucket. |
| **Resume Text Extraction**| Synchronous in-app extraction (`pypdf`) | **AWS Lambda** (S3 Event-driven) | Switch to async S3 event trigger triggering Lambda `resume_processor` with SQS queue. |
| **Notifications & Alerts**| In-memory / DB logs | **Amazon SNS** / Amazon SES | Create `NotificationService` adapter publishing SNS topics or sending SES candidate status emails. |
| **Monitoring & Logging** | Python `logging` to stdout/files | **Amazon CloudWatch** Logs & Metrics | Attach AWS CloudWatch agent / AWS OpenTelemetry SDK to stream logs and system metrics. |
| **Security & Access** | Local JWT & Bcrypt | **AWS IAM** & Cognito (optional) | IAM roles for EC2/Lambda service execution; keep custom role JWT or integrate Cognito user pools. |
| **Generative AI** | Google Gemini API (Configurable LLM) | **Amazon Bedrock** / Gemini | LLM service interface (`LLMService`) abstracts provider; plug in `boto3` Bedrock runtime if desired. |

## Abstraction Boundary Strategy
To enable seamless AWS migration without refactoring core business logic:
- `app/services/storage_service.py` provides an abstract base class `StorageService` (`LocalStorageService` currently used, `S3StorageService` drop-in replacement).
- `app/core/database.py` relies strictly on standard SQLAlchemy Engine and Session scopes.
- `app/services/llm_service.py` encapsulates all prompt formatting, LLM invocation, schema validation, and fallback mechanisms.
