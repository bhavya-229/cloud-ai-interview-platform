import os
import io
import json
import urllib.parse
import logging
import boto3
from pypdf import PdfReader
import psycopg2

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
sns_client = boto3.client("sns")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF in memory using pypdf."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text.strip())
    extracted = "\n\n".join(text_parts).strip()
    return extracted or "No readable text extracted (scanned or image-only PDF)."


def lambda_handler(event, context):
    """S3 Event-triggered AWS Lambda handler for asynchronous resume processing.
    
    Trigger: S3 ObjectCreated (Put)
    Actions:
      1. Fetch PDF from S3.
      2. Extract resume text.
      3. Persist record into Amazon RDS PostgreSQL.
      4. Emit SNS notification.
    """
    logger.info("Received event: %s", json.dumps(event))

    for record in event.get("Records", []):
        bucket_name = record["s3"]["bucket"]["name"]
        object_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        logger.info(f"Processing S3 object: s3://{bucket_name}/{object_key}")

        # Only process PDF files
        if not object_key.lower().endswith(".pdf"):
            logger.warning(f"Skipping non-pdf file: {object_key}")
            continue

        try:
            # 1. Download file from S3
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            pdf_bytes = response["Body"].read()

            # 2. Extract plain text
            extracted_text = extract_text_from_pdf(pdf_bytes)
            logger.info(f"Successfully extracted {len(extracted_text)} characters from {object_key}")

            # 3. Parse candidate ID from key convention (e.g. candidate_12/uuid_name.pdf)
            candidate_id = None
            parts = object_key.split("/")
            if len(parts) > 1 and parts[0].startswith("candidate_"):
                try:
                    candidate_id = int(parts[0].replace("candidate_", ""))
                except ValueError:
                    pass

            file_name = parts[-1] if parts else object_key

            # 4. Save to Amazon RDS PostgreSQL (if DATABASE_URL configured)
            if DATABASE_URL and candidate_id:
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                s3_path = f"s3://{bucket_name}/{object_key}"
                cursor.execute("SELECT id FROM resumes WHERE file_path = %s", (s3_path,))
                row = cursor.fetchone()
                if row:
                    cursor.execute("UPDATE resumes SET extracted_text = %s, uploaded_at = NOW() WHERE id = %s", (extracted_text, row[0]))
                    logger.info(f"Updated existing resume record #{row[0]} with extracted text.")
                else:
                    insert_query = """
                        INSERT INTO resumes (candidate_id, file_name, file_path, extracted_text, uploaded_at)
                        VALUES (%s, %s, %s, %s, NOW())
                    """
                    cursor.execute(insert_query, (candidate_id, file_name, s3_path, extracted_text))
                    logger.info(f"Saved resume record into RDS for candidate ID: {candidate_id}")
                conn.commit()
                cursor.close()
                conn.close()

            # 5. Emit SNS Alert (if SNS_TOPIC_ARN configured)
            if SNS_TOPIC_ARN:
                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject=f"Resume Processed: {file_name}",
                    Message=f"Resume file '{file_name}' for Candidate #{candidate_id or 'Unknown'} has been processed and indexed into RDS."
                )

        except Exception as e:
            logger.error(f"Error processing resume {object_key}: {str(e)}", exc_info=True)
            raise e

    return {"status": "success", "processed_records": len(event.get("Records", []))}
