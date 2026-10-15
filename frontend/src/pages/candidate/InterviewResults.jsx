import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../../services/api';
import Alert from '../../components/Alert';
import { Award, CheckCircle2, AlertTriangle, BookOpen, FileText, ArrowLeft } from 'lucide-react';

export default function InterviewResults() {
  const { id } = useParams();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchResults();
  }, [id]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      const data = await api.getInterviewResults(id);
      setResults(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch interview results.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner-container">
        <div className="spinner"></div>
        <p>Generating Assessment Report...</p>
      </div>
    );
  }

  const report = results?.assessment_report || {};

  return (
    <div className="page-container max-w-5xl">
      <div className="mb-4">
        <Link to="/candidate/dashboard" className="back-link flex items-center gap-1 text-sm text-muted">
          <ArrowLeft size={16} /> Back to Dashboard
        </Link>
      </div>

      <Alert type="error" message={error} />

      {/* Main Scorecard Banner */}
      <div className="results-hero-card">
        <div className="hero-left">
          <div className="score-circle-large">
            <span className="score-number">{results?.overall_score?.toFixed(1) || '0.0'}</span>
            <span className="score-sub">/ 10</span>
          </div>
          <div>
            <span className="results-role-badge">{results?.job_title}</span>
            <h1 className="results-title">Assessment Report</h1>
            <p className="results-date">
              Completed on {results?.completed_at ? new Date(results.completed_at).toLocaleString() : 'N/A'}
            </p>
          </div>
        </div>

        <div className="hero-right">
          <div className="rec-box">
            <span className="rec-label">Recommendation</span>
            <span className={`rec-badge rec-${report.recommendation?.toLowerCase().replace(/\s+/g, '-')}`}>
              {report.recommendation || 'Evaluated'}
            </span>
          </div>
        </div>
      </div>

      {/* Synthesis Report Grid */}
      <div className="results-summary-card mt-6">
        <h3 className="section-title">Performance Summary</h3>
        <p className="summary-paragraph">{report.overall_performance}</p>
        {report.interview_summary && (
          <p className="summary-paragraph text-muted mt-2">{report.interview_summary}</p>
        )}

        <div className="report-columns-grid mt-6">
          <div className="report-col col-strengths">
            <div className="col-header text-green-700">
              <CheckCircle2 size={18} />
              <h4>Technical Strengths</h4>
            </div>
            <ul>
              {report.technical_strengths?.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="report-col col-weaknesses">
            <div className="col-header text-amber-700">
              <AlertTriangle size={18} />
              <h4>Weak Areas</h4>
            </div>
            <ul>
              {report.weak_areas?.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="report-col col-topics">
            <div className="col-header text-blue-700">
              <BookOpen size={18} />
              <h4>Recommended Topics to Improve</h4>
            </div>
            <ul>
              {report.topics_to_improve?.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Transcript Breakdown */}
      <div className="breakdown-section mt-8">
        <h3 className="section-title mb-4">Detailed Question Breakdown</h3>

        <div className="breakdown-list">
          {results?.breakdown?.map((item, idx) => (
            <div key={idx} className="breakdown-card">
              <div className="breakdown-header">
                <div>
                  <span className="q-tag">Question #{item.sequence_number}</span>
                  <span className="difficulty-tag">{item.difficulty}</span>
                </div>
                <div className="q-score">
                  Score: <strong>{item.score} / 10</strong>
                </div>
              </div>

              <div className="breakdown-question">
                <strong>Question:</strong> {item.question_text}
              </div>

              <div className="breakdown-answer">
                <strong>Your Answer:</strong>
                <p>{item.answer_text}</p>
              </div>

              {item.evaluation && (
                <div className="breakdown-feedback">
                  <strong>AI Feedback:</strong>
                  <p>{item.evaluation.feedback}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
