import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service to publish real-time alerts to Amazon SNS topics.
    
    Ensures notifications for interview events (completion, assessment readiness)
    flow to subscribers while failing gracefully if SNS is not configured or offline.
    """

    def __init__(self, topic_arn: Optional[str] = None, region_name: Optional[str] = None):
        self.topic_arn = topic_arn or settings.SNS_TOPIC_ARN
        self.region_name = region_name or settings.AWS_REGION
        self._sns_client = None

        if self.topic_arn:
            try:
                import boto3
                self._sns_client = boto3.client("sns", region_name=self.region_name)
                logger.info(f"SNS notification service initialized for topic: {self.topic_arn}")
            except Exception as e:
                logger.warning(f"Could not initialize Amazon SNS client: {e}")

    def publish_event(self, subject: str, message: str) -> bool:
        """Publish message to configured SNS topic."""
        if not self._sns_client or not self.topic_arn:
            logger.debug(f"[Local Notification Log] {subject}: {message}")
            return False

        try:
            self._sns_client.publish(
                TopicArn=self.topic_arn,
                Subject=subject[:100],
                Message=message
            )
            logger.info(f"Published SNS alert: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish SNS notification: {e}")
            return False

    def notify_interview_completed(
        self,
        candidate_name: str,
        job_title: str,
        overall_score: float,
        recommendation: str,
        interview_id: int
    ):
        subject = f"Interview Completed: {candidate_name} for {job_title}"
        message = (
            f"Candidate Assessment Notification\n\n"
            f"Candidate: {candidate_name}\n"
            f"Job Position: {job_title}\n"
            f"Overall Score: {overall_score:.1f} / 10.0\n"
            f"Recommendation: {recommendation}\n"
            f"Interview ID: {interview_id}\n\n"
            f"Login to the Recruiter Portal to view the complete assessment scorecard."
        )
        return self.publish_event(subject=subject, message=message)

    def notify_resume_processed(self, candidate_name: str, filename: str, success: bool):
        subject = f"Resume Processed: {candidate_name}"
        status_text = "successfully extracted and ready for interviews" if success else "failed text extraction"
        message = f"Resume file '{filename}' for candidate {candidate_name} was {status_text}."
        return self.publish_event(subject=subject, message=message)


# Singleton factory
notification_service = NotificationService()
