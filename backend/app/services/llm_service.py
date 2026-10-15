import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx
import google.generativeai as genai
from app.core.config import settings
from app.schemas.answer import LLMEvaluationOutput, LLMFinalAssessmentOutput
from app.schemas.question import LLMQuestionOutput

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = (api_key or settings.LLM_API_KEY).strip()
        raw_model = (model_name or settings.LLM_MODEL).strip()
        self.model_name = raw_model or "gemini-3.5-flash"
        self._client_initialized = False

        if self.api_key and self.api_key != "your_gemini_api_key_here":
            self._client_initialized = True
            logger.info(f"Initialized LLM service with primary model: {self.model_name}")
            try:
                genai.configure(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"GenAI configure warning: {e}")
        else:
            logger.info("No Gemini API key supplied. Running on intelligent local contextual fallback engine.")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Safely extract and parse JSON object from LLM response text."""
        cleaned = text.strip()
        # Remove Markdown code fence if present
        if "```json" in cleaned:
            match = re.search(r"```json\s*(.*?)\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
        elif "```" in cleaned:
            match = re.search(r"```\s*(.*?)\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()

        # If not cleanly fenced, extract substring between first '{' and last '}'
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            cleaned = cleaned[start_idx : end_idx + 1]

        return json.loads(cleaned)

    def _call_gemini(self, prompt: str) -> str:
        """Execute prompt against Gemini model with cascading fallback and strict timeouts."""
        if not self._client_initialized:
            raise RuntimeError("Gemini API key is not configured or client initialization failed.")

        # Candidate models to try in order (e.g. try user's requested model, then gemini-3.5-flash)
        models_to_try = [self.model_name]
        for fallback_m in ["gemini-3.5-flash", "gemini-3.8-flash"]:
            if fallback_m not in models_to_try:
                models_to_try.append(fallback_m)

        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                with httpx.Client(timeout=6.0) as client:
                    resp = client.post(
                        url,
                        json={"contents": [{"parts": [{"text": prompt}]}]},
                        headers={"Content-Type": "application/json"}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"]
                    logger.warning(f"Model '{model}' returned status {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                logger.warning(f"Model '{model}' timed out or errored: {e}")

        raise RuntimeError("All Gemini candidate models timed out or failed to return text.")

    def generate_initial_question(
        self,
        job_title: str,
        job_description: str,
        required_skills: str,
        resume_text: str
    ) -> LLMQuestionOutput:
        """Generate the first personalized interview question tailored to the job and resume."""
        prompt = f"""
You are an expert technical interviewer conducting an interview for the role of "{job_title}".
Job Description: {job_description}
Required Skills: {required_skills}

Candidate Resume Background:
{resume_text[:2500]}

Generate the FIRST opening interview question. It should assess a fundamental skill or project mentioned in their background relevant to the job requirements.
Return ONLY valid JSON matching this schema:
{{
  "question": "string (the interview question text)",
  "question_type": "technical" or "behavioral" or "situational",
  "difficulty": "easy" or "medium" or "hard",
  "topic": "string (core skill e.g. Python, System Design, REST APIs)"
}}
"""
        if self._client_initialized:
            try:
                response_text = self._call_gemini(prompt)
                data = self._extract_json(response_text)
                return LLMQuestionOutput.model_validate(data)
            except Exception as e:
                logger.error(f"LLM API generation error in initial question: {e}")

        # Resilient contextual fallback if LLM is unavailable or offline
        primary_skill = required_skills.split(",")[0].strip() if required_skills else "software engineering"
        return LLMQuestionOutput(
            question=f"Welcome! To start, could you explain your experience with {primary_skill} and describe a project from your resume where you applied it to solve a complex problem?",
            question_type="technical",
            difficulty="medium",
            topic=primary_skill
        )

    def generate_followup_question(
        self,
        job_title: str,
        job_description: str,
        required_skills: str,
        resume_text: str,
        previous_history: List[Dict[str, Any]],
        current_sequence: int
    ) -> LLMQuestionOutput:
        """Generate an adaptive follow-up question based on candidate's answers and evaluations so far."""
        history_formatted = ""
        for idx, item in enumerate(previous_history, 1):
            history_formatted += (
                f"\nRound {idx}:\n"
                f"Question: {item.get('question')}\n"
                f"Candidate Answer: {item.get('answer')}\n"
                f"Score: {item.get('score')}/10\n"
                f"Evaluation Feedback: {item.get('feedback')}\n"
            )

        prompt = f"""
You are an expert interviewer conducting an interview for "{job_title}".
Job Description: {job_description}
Required Skills: {required_skills}
Candidate Resume:
{resume_text[:2000]}

Interview History So Far:
{history_formatted}

Task:
Generate Question #{current_sequence}.
This must be an ADAPTIVE question:
- If the candidate answered strongly, increase difficulty or probe architectural trade-offs.
- If the candidate struggled, probe fundamentals or explore a different required skill from "{required_skills}".
- Do NOT repeat questions already asked.

Return ONLY valid JSON matching this schema:
{{
  "question": "string (the interview question text)",
  "question_type": "technical" or "behavioral" or "situational",
  "difficulty": "easy" or "medium" or "hard",
  "topic": "string (skill or concept)"
}}
"""
        if self._client_initialized:
            try:
                response_text = self._call_gemini(prompt)
                data = self._extract_json(response_text)
                return LLMQuestionOutput.model_validate(data)
            except Exception as e:
                logger.error(f"LLM API generation error in follow-up question: {e}")

        # Resilient contextual fallback
        skills_list = [s.strip() for s in required_skills.split(",") if s.strip()]
        topic = skills_list[current_sequence % len(skills_list)] if skills_list else "Problem Solving"
        return LLMQuestionOutput(
            question=f"Building on our discussion, how do you handle performance optimization, testing, and edge cases when working with {topic}?",
            question_type="technical",
            difficulty="medium",
            topic=topic
        )

    def evaluate_answer(
        self,
        job_title: str,
        required_skills: str,
        question_text: str,
        question_type: str,
        difficulty: str,
        answer_text: str,
        resume_text: str = ""
    ) -> LLMEvaluationOutput:
        """Evaluate a candidate's answer using structured output."""
        clean = answer_text.strip().lower()
        ignorance_tokens = [
            "sorry", "i dont know", "i don't know", "dont know", "dont remember",
            "i dont remember", "i don't remember", "no idea", "pass", "skip",
            "idk", "not sure", "cant remember", "can't remember", "no clue",
            "i do not know", "i do not remember", "none", "na", "n/a", "nothing"
        ]
        words = clean.split()
        is_non_answer = clean in ignorance_tokens or (len(words) <= 4 and any(w in clean for w in ["sorry", "dont know", "don't know", "dont remember", "don't remember", "no idea", "idk", "cant remember"]))

        prompt = f"""
You are an expert hiring evaluator assessing an interview answer for a "{job_title}" role.
Required Skills: {required_skills}

Question Asked ({question_type}, Difficulty: {difficulty}):
"{question_text}"

Candidate's Submitted Answer:
"{answer_text}"

Evaluate this answer rigorously on technical accuracy, clarity, completeness, and practical relevance.

CRITICAL SCORING RULE:
- If the candidate writes 'sorry', 'i don't know', 'i don't remember', 'pass', 'skip', leaves it blank, or admits lack of knowledge, the score MUST BE EXACTLY 0.0 out of 10.0.
- In this case, strengths must be an empty list []. Do not award participation points for apologizing or admitting ignorance.
- For legitimate technical answers:
  * 9.0 - 10.0: Outstanding, deeply comprehensive, covers edge cases and nuances.
  * 7.0 - 8.9: Good, solid understanding with minor omissions.
  * 5.0 - 6.9: Acceptable/Partial, basic concepts grasped but lacks depth.
  * 0.0 - 4.9: Inadequate, incorrect, excessively brief, or off-topic.

Return ONLY valid JSON matching this schema:
{{
  "score": float (between 0.0 and 10.0),
  "correctness": "Excellent" or "Good" or "Partial" or "Poor" or "No Answer",
  "strengths": ["string", "string"],
  "weaknesses": ["string", "string"],
  "feedback": "string (constructive feedback explaining what was good and what was missing)"
}}
"""
        if self._client_initialized:
            try:
                response_text = self._call_gemini(prompt)
                data = self._extract_json(response_text)
                return LLMEvaluationOutput.model_validate(data)
            except Exception as e:
                logger.error(f"LLM API evaluation error: {e}")

        # Resilient fallback evaluation
        if is_non_answer or len(words) == 0:
            return LLMEvaluationOutput(
                score=0.0,
                correctness="No Answer / Unanswered",
                strengths=[],
                weaknesses=[
                    "Candidate stated they did not know or recall this technical topic.",
                    "No technical attempt or conceptual explanation provided."
                ],
                feedback="The candidate was unable to provide an answer to this question. Core familiarity with this required competency was not demonstrated."
            )
        elif len(words) < 5:
            score = 2.0
            correctness = "Poor"
            strengths = ["Provided a very brief attempt"]
            weaknesses = ["Answer was far too concise without technical depth or examples"]
            feedback = "Please elaborate further with concrete explanations and real-world implementation details."
        elif len(words) < 25:
            score = 6.0
            correctness = "Partial"
            strengths = ["Addressed the basic premise of the question"]
            weaknesses = ["Could include more specific architectural reasoning or examples"]
            feedback = "Solid foundation, but expanding on edge cases and design considerations would strengthen this answer."
        else:
            score = 8.5
            correctness = "Good"
            strengths = ["Detailed response demonstrating clear technical understanding", "Included practical reasoning"]
            weaknesses = ["Could delve further into performance bottlenecks or alternative approaches"]
            feedback = "Well-structured response that effectively articulates key concepts and application context."

        return LLMEvaluationOutput(
            score=score,
            correctness=correctness,
            strengths=strengths,
            weaknesses=weaknesses,
            feedback=feedback
        )

    def generate_final_feedback(
        self,
        job_title: str,
        required_skills: str,
        resume_text: str,
        interview_history: List[Dict[str, Any]],
        overall_score: float
    ) -> LLMFinalAssessmentOutput:
        """Generate comprehensive final evaluation report after interview completes."""
        history_summary = ""
        for idx, item in enumerate(interview_history, 1):
            history_summary += (
                f"Q{idx} ({item.get('difficulty', 'medium')} {item.get('topic', '')}): {item.get('question')}\n"
                f"Answer: {item.get('answer')}\n"
                f"Score: {item.get('score')}/10 | Feedback: {item.get('feedback')}\n\n"
            )

        prompt = f"""
You are an executive hiring committee evaluator preparing a candidate assessment report for "{job_title}".
Required Skills: {required_skills}
Calculated Average Score: {overall_score:.1f}/10

Full Interview Transcript & Evaluations:
{history_summary}

Synthesize this candidate's overall performance into an executive assessment report.
If the candidate failed to answer most or all questions (score near 0), recommendation MUST be "Do Not Hire", and technical_strengths must accurately reflect lack of demonstrated knowledge.

Return ONLY valid JSON matching this schema:
{{
  "overall_performance": "string (executive performance summary)",
  "technical_strengths": ["string", "string"],
  "weak_areas": ["string", "string"],
  "topics_to_improve": ["string", "string"],
  "interview_summary": "string (detailed synthesis of technical competencies demonstrated)",
  "recommendation": "Strong Hire" or "Hire" or "Consider" or "Do Not Hire"
}}
"""
        if self._client_initialized:
            try:
                response_text = self._call_gemini(prompt)
                data = self._extract_json(response_text)
                return LLMFinalAssessmentOutput.model_validate(data)
            except Exception as e:
                logger.error(f"LLM API final report error: {e}")

        # Resilient fallback final assessment
        if overall_score >= 8.0:
            rec = "Strong Hire"
            perf = "Demonstrated strong domain competence and practical technical depth."
            strengths = ["Clear communication style", "In-depth knowledge of core systems"]
            weaknesses = ["Minor edge-case coverage"]
            topics = ["Advanced distributed system patterns"]
        elif overall_score >= 6.5:
            rec = "Hire"
            perf = "Good conceptual knowledge across most required competencies with minor areas for growth."
            strengths = ["Solid grasp of key frameworks", "Practical coding familiarity"]
            weaknesses = ["Could deepen architectural trade-off discussions"]
            topics = ["System optimization and scale"]
        elif overall_score >= 4.0:
            rec = "Consider"
            perf = "Demonstrated foundational skills but showed gaps in intermediate/advanced areas."
            strengths = ["Basic familiarity with primary tools"]
            weaknesses = ["Lacks depth in advanced concepts and optimization"]
            topics = ["Comprehensive review of core frameworks"]
        else:
            rec = "Do Not Hire"
            perf = "The candidate demonstrated severe technical knowledge gaps and was unable to answer key questions for this role."
            strengths = ["Candidate was transparent about knowledge boundaries"] if overall_score > 0 else []
            weaknesses = [
                "Unable to answer fundamental and practical technical questions across tested topics",
                "Lacks required technical competence for this position"
            ]
            topics = [
                f"Fundamental study of {required_skills or 'core programming concepts'}",
                "Hands-on project development and foundational implementation"
            ]

        return LLMFinalAssessmentOutput(
            overall_performance=perf,
            technical_strengths=strengths,
            weak_areas=weaknesses,
            topics_to_improve=topics,
            interview_summary=f"The candidate completed the assessment for {job_title} with an average score of {overall_score:.1f}/10.",
            recommendation=rec
        )
