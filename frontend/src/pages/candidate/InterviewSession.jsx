import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import Alert from '../../components/Alert';
import { MessageSquare, Send, CheckCircle2, AlertTriangle, ArrowRight, Award } from 'lucide-react';

export default function InterviewSession() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [interview, setInterview] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [answerText, setAnswerText] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [evaluationResult, setEvaluationResult] = useState(null);

  useEffect(() => {
    fetchInterviewDetails();
  }, [id]);

  const fetchInterviewDetails = async () => {
    try {
      setLoading(true);
      const data = await api.getInterview(id);
      setInterview(data);

      if (data.status === 'completed') {
        navigate(`/candidate/interview/${id}/results`);
        return;
      }

      // Find first unanswered question
      const unanswered = data.questions.find((q) => !q.answers || q.answers.length === 0);
      if (unanswered) {
        setCurrentQuestion(unanswered);
      } else if (data.questions.length > 0) {
        // Last question was answered but still in progress
        setCurrentQuestion(data.questions[data.questions.length - 1]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load interview session.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSubmit = async (e) => {
    e.preventDefault();
    if (!answerText.trim() || !currentQuestion) return;

    setSubmitting(true);
    setError('');

    try {
      const res = await api.submitAnswer(id, currentQuestion.id, answerText);
      setEvaluationResult(res);
      setAnswerText('');
    } catch (err) {
      setError(err.message || 'Failed to submit answer.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleProceed = () => {
    if (!evaluationResult) return;

    if (evaluationResult.is_completed) {
      navigate(`/candidate/interview/${id}/results`);
    } else if (evaluationResult.next_question) {
      setCurrentQuestion(evaluationResult.next_question);
      setEvaluationResult(null);
    } else {
      fetchInterviewDetails();
      setEvaluationResult(null);
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner-container">
        <div className="spinner"></div>
        <p>Loading AI Interview Session...</p>
      </div>
    );
  }

  return (
    <div className="interview-container">
      {/* Interview Top Navigation / Progress */}
      <div className="interview-session-header">
        <div>
          <span className="interview-role-tag">{interview?.job?.title}</span>
          <h2>AI Technical Interview</h2>
        </div>
        <div className="interview-progress-badge">
          Round {currentQuestion?.sequence_number || 1}
        </div>
      </div>

      <Alert type="error" message={error} />

      {/* Main Q&A Area */}
      <div className="interview-card">
        {/* Question Header */}
        <div className="question-box">
          <div className="question-meta-bar">
            <span className="question-num-tag">
              Question #{currentQuestion?.sequence_number || 1}
            </span>
            <span className={`difficulty-badge diff-${currentQuestion?.difficulty || 'medium'}`}>
              {currentQuestion?.difficulty || 'Medium'}
            </span>
            <span className="type-badge">{currentQuestion?.question_type || 'Technical'}</span>
          </div>

          <div className="question-text">
            {currentQuestion?.question_text}
          </div>
        </div>

        {/* Evaluation Feedback Modal / Inline Display */}
        {evaluationResult ? (
          <div className="evaluation-feedback-panel">
            <div className="eval-header">
              <div className="eval-score-ring">
                <span className="score-val">{evaluationResult.evaluation.score}</span>
                <span className="score-max">/10</span>
              </div>
              <div>
                <h3>AI Round Evaluation</h3>
                <span className="correctness-tag">
                  Assessment: {evaluationResult.evaluation.correctness}
                </span>
              </div>
            </div>

            <div className="eval-feedback-text">
              <p>{evaluationResult.evaluation.feedback}</p>
            </div>

            <div className="eval-details-grid">
              {evaluationResult.evaluation.strengths?.length > 0 && (
                <div className="eval-block strengths">
                  <div className="eval-block-title text-green-700">
                    <CheckCircle2 size={16} /> Key Strengths
                  </div>
                  <ul>
                    {evaluationResult.evaluation.strengths.map((s, idx) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}

              {evaluationResult.evaluation.weaknesses?.length > 0 && (
                <div className="eval-block weaknesses">
                  <div className="eval-block-title text-amber-700">
                    <AlertTriangle size={16} /> Areas to Improve
                  </div>
                  <ul>
                    {evaluationResult.evaluation.weaknesses.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="eval-action-bar">
              <button onClick={handleProceed} className="btn-primary flex items-center gap-2">
                {evaluationResult.is_completed ? (
                  <>
                    <Award size={18} /> View Final Assessment Report
                  </>
                ) : (
                  <>
                    <span>Next Question</span> <ArrowRight size={18} />
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          /* Answer Input Form */
          <form onSubmit={handleAnswerSubmit} className="answer-form">
            <div className="form-group">
              <label htmlFor="answer">
                Your Answer <span className="text-muted text-xs font-normal">(Be specific and technical)</span>
              </label>
              <textarea
                id="answer"
                rows={7}
                placeholder="Type your detailed technical explanation here..."
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                required
                disabled={submitting}
              />
            </div>

            <div className="answer-form-actions">
              <div className="answer-tip text-muted text-xs">
                💡 Tip: Mention relevant tools, algorithms, edge-cases, or system trade-offs.
              </div>
              <button
                type="submit"
                className="btn-primary flex items-center gap-2"
                disabled={submitting || !answerText.trim()}
              >
                {submitting ? (
                  <>
                    <div className="spinner-sm"></div>
                    AI is evaluating your response...
                  </>
                ) : (
                  <>
                    <Send size={16} /> Submit Answer
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
