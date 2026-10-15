# Database Architecture & Evolution

## Local Phase: SQLite via SQLAlchemy ORM
In the local development phase, the application connects to a file-based SQLite database (`sqlite:///./sql_app.db` or configured via `DATABASE_URL`).
All tables are defined strictly through SQLAlchemy ORM models (`app/models/`), using standard relational conventions:
- Foreign keys (`user.id`, `job.id`, `interview.id`, `question.id`)
- Cascade deletes where appropriate
- Indexed queries on foreign keys and primary keys

Because all queries flow through SQLAlchemy ORM sessions without raw SQLite-specific syntax, migrating to Amazon RDS requires only changing the `DATABASE_URL` connection string and database driver.

## Future AWS Phase: Amazon RDS (PostgreSQL / MySQL)
In the production cloud deployment:
1. An Amazon RDS PostgreSQL (or Aurora Serverless v2) instance will be provisioned in private subnets within the VPC.
2. The FastAPI application will connect via `postgresql+asyncpg://` or `postgresql://` using AWS Secrets Manager for credential management.
3. Database migrations will be managed using Alembic to support automated schema evolution across environments.
