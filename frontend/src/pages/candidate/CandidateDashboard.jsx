import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';
import Alert from '../../components/Alert';
import { Briefcase, CheckCircle2, Clock, FileText, ArrowRight, Award } from 'lucide-react';

export default function CandidateDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.getCandidateDashboard();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading-spinner-container"><div className="spinner"></div><p>Loading your dashboard...</p></div>;
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <h1>Welcome, {data?.candidate?.name}</h1>
          <p className="subtitle">Track your AI interviews and technical evaluations</p>
        </div>
        <div className="header-actions">
          <Link to="/candidate/resume" className="btn-secondary">
            <FileText size={16} /> Manage Resume
          </Link>
          <Link to="/candidate/jobs" className="btn-primary">
            <Briefcase size={16} /> Browse Open Roles
          </Link>
        </div>
      </div>

      <Alert type="error" message={error} />

      {/* Stats row */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-wrapper blue">
            <Briefcase size={22} />
          </div>
          <div>
            <div className="stat-value">{data?.stats?.available_jobs || 0}</div>
            <div className="stat-label">Available Jobs</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper green">
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div className="stat-value">{data?.stats?.completed_interviews || 0}</div>
            <div className="stat-label">Completed Interviews</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper orange">
            <Clock size={22} />
          </div>
          <div>
            <div className="stat-value">{data?.stats?.in_progress_interviews || 0}</div>
            <div className="stat-label">In Progress</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper purple">
            <Award size={22} />
          </div>
          <div>
            <div className="stat-value">{data?.stats?.has_resume ? 'Uploaded' : 'Missing'}</div>
            <div className="stat-label">Resume Status</div>
          </div>
        </div>
      </div>

      {/* Resume Banner if not uploaded */}
      {!data?.stats?.has_resume && (
        <div className="info-banner warning-banner">
          <div>
            <h4>Upload your resume for personalized questions</h4>
            <p>Our AI interviewer tailors interview questions to your background and experience.</p>
          </div>
          <Link to="/candidate/resume" className="btn-warning">Upload Resume</Link>
        </div>
      )}

      {/* Recent Interviews Section */}
      <div className="section-card">
        <div className="section-header">
          <h3>Your Interview History</h3>
          <Link to="/candidate/jobs" className="section-link">Find More Roles <ArrowRight size={14} /></Link>
        </div>

        {(!data?.recent_interviews || data.recent_interviews.length === 0) ? (
          <div className="empty-state">
            <p>You haven't participated in any interviews yet.</p>
            <Link to="/candidate/jobs" className="btn-primary">Browse Available Jobs & Start</Link>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Job Title</th>
                  <th>Status</th>
                  <th>Overall Score</th>
                  <th>Started</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_interviews.map((item) => (
                  <tr key={item.id}>
                    <td className="font-semibold">{item.job?.title || `Job #${item.job_id}`}</td>
                    <td>
                      <span className={`status-pill status-${item.status}`}>
                        {item.status === 'completed' ? 'Completed' : 'In Progress'}
                      </span>
                    </td>
                    <td>
                      {item.overall_score !== null ? (
                        <span className="score-badge">{item.overall_score} / 10</span>
                      ) : (
                        <span className="text-muted">Pending</span>
                      )}
                    </td>
                    <td>{new Date(item.started_at).toLocaleDateString()}</td>
                    <td>
                      {item.status === 'completed' ? (
                        <Link to={`/candidate/interview/${item.id}/results`} className="btn-sm btn-outline">
                          View Report
                        </Link>
                      ) : (
                        <Link to={`/candidate/interview/${item.id}`} className="btn-sm btn-primary">
                          Continue Interview
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
