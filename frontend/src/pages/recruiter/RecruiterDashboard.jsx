import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';
import Alert from '../../components/Alert';
import { Briefcase, Users, CheckCircle2, Clock, PlusCircle, ArrowRight, Award } from 'lucide-react';

export default function RecruiterDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.getRecruiterDashboard();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load recruiter dashboard.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner-container">
        <div className="spinner"></div>
        <p>Loading recruiter analytics...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <h1>Recruiter Portal</h1>
          <p className="subtitle">Manage job openings and evaluate AI candidate assessments</p>
        </div>
        <div className="header-actions">
          <Link to="/recruiter/jobs" className="btn-primary">
            <PlusCircle size={16} /> Post New Job
          </Link>
          <Link to="/recruiter/candidates" className="btn-secondary">
            <Users size={16} /> View Candidates
          </Link>
        </div>
      </div>

      <Alert type="error" message={error} />

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon-wrapper blue">
            <Briefcase size={22} />
          </div>
          <div>
            <div className="stat-value">{data?.stats?.jobs_posted || 0}</div>
            <div className="stat-label">Jobs Posted</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper purple">
            <Users size={22} />
          </div>
          <div>
            <div className="stat-value">{data?.stats?.total_interviews || 0}</div>
            <div className="stat-label">Total Interviews</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon-wrapper green">
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div className="stat-value">{data?.stats?.completed_assessments || 0}</div>
            <div className="stat-label">Completed Assessments</div>
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
      </div>

      {/* Recent Interviews Table */}
      <div className="section-card mt-6">
        <div className="section-header">
          <h3>Recent Candidate Assessments</h3>
          <Link to="/recruiter/candidates" className="section-link">
            All Candidates <ArrowRight size={14} />
          </Link>
        </div>

        {(!data?.recent_interviews || data.recent_interviews.length === 0) ? (
          <div className="empty-state">
            <p>No interviews have been started yet for your jobs.</p>
            <Link to="/recruiter/jobs" className="btn-primary">Create or Share Job Postings</Link>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Job Title</th>
                  <th>Candidate</th>
                  <th>Status</th>
                  <th>Overall Score</th>
                  <th>Date</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_interviews.map((item) => (
                  <tr key={item.id}>
                    <td className="font-semibold">{item.job?.title || `Job #${item.job_id}`}</td>
                    <td>{item.candidate?.name || `Candidate #${item.candidate_id}`}</td>
                    <td>
                      <span className={`status-pill status-${item.status}`}>
                        {item.status === 'completed' ? 'Completed' : 'In Progress'}
                      </span>
                    </td>
                    <td>
                      {item.overall_score !== null ? (
                        <span className="score-badge">{item.overall_score} / 10</span>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td>{new Date(item.started_at).toLocaleDateString()}</td>
                    <td>
                      {item.status === 'completed' ? (
                        <Link to={`/recruiter/interviews/${item.id}/report`} className="btn-sm btn-outline">
                          View AI Report
                        </Link>
                      ) : (
                        <span className="text-xs text-muted">Interview Active</span>
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
