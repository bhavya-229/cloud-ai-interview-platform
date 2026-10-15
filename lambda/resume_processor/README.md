# AWS Lambda Resume Processor (Future Cloud Phase)

## Overview
During the local phase, resume parsing is executed locally and synchronously using `pypdf` through `LocalStorageService` and `ResumeService`.

## Cloud Target Design
In the AWS production phase:
1. Candidate uploads a PDF resume from the React client directly or via pre-signed URL to an Amazon S3 bucket (`s3://ai-interview-resumes/candidate_id/`).
2. An S3 `ObjectCreated` event triggers this AWS Lambda function (`resume_processor`).
3. The Lambda function:
   - Downloads the PDF stream from S3 or processes it in-memory.
   - Extracts text using PyMuPDF / Textract.
   - Summarizes or indexes candidate skills using an AWS Lambda layer or calls the LLM.
   - Writes the parsed metadata and text back to the Amazon RDS database.
   - Emits an Amazon SNS event to notify recruiters or update application statuses.
4. The local `StorageService` interface (`upload_file`, `get_file`, `delete_file`) and `ResumeService` decouple the application core from this underlying event-driven shift.
