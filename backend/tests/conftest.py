import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from pypdf import PdfWriter

from app.core.database import Base, get_db
from app.main import app
from app.schemas.question import LLMQuestionOutput
from app.schemas.answer import LLMEvaluationOutput, LLMFinalAssessmentOutput
from app.services.llm_service import LLMService
from app.api.routes import interviews

# In-memory SQLite for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class MockLLMService:
    """Mock LLM Service to allow test execution without external API dependencies."""

    def __init__(self, *args, **kwargs):
        pass

    def generate_initial_question(self, job_title, job_description, required_skills, resume_text):
        return LLMQuestionOutput(
            question=f"Explain your background in {required_skills.split(',')[0]} and how it applies to {job_title}.",
            question_type="technical",
            difficulty="medium",
            topic="Core Competency"
        )

    def generate_followup_question(self, job_title, job_description, required_skills, resume_text, previous_history, current_sequence):
        return LLMQuestionOutput(
            question=f"Question #{current_sequence}: How would you optimize query latency in this architecture?",
            question_type="technical",
            difficulty="hard",
            topic="Optimization"
        )

    def evaluate_answer(self, job_title, required_skills, question_text, question_type, difficulty, answer_text, resume_text=""):
        return LLMEvaluationOutput(
            score=8.5,
            correctness="Good",
            strengths=["Concise technical explanation", "Directly addressed prompt"],
            weaknesses=["Could explore concurrency issues"],
            feedback="Strong demonstration of fundamentals."
        )

    def generate_final_feedback(self, job_title, required_skills, resume_text, interview_history, overall_score):
        return LLMFinalAssessmentOutput(
            overall_performance="Candidate demonstrated consistently high proficiency.",
            technical_strengths=["Clear logic", "Good domain knowledge"],
            weak_areas=["Edge case handling"],
            topics_to_improve=["Distributed systems"],
            interview_summary=f"Completed {len(interview_history)} rounds with an average score of {overall_score}.",
            recommendation="Hire"
        )


@pytest.fixture(scope="session", autouse=True)
def override_llm_service():
    """Inject mock LLM service into interview router and services."""
    mock_llm = MockLLMService()
    interviews.interview_service.llm = mock_llm
    interviews.interview_service.assessment.llm = mock_llm
    yield


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_bytes():
    """Generate in-memory valid PDF bytes for resume upload testing."""
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()
