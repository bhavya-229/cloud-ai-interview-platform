import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../../services/api';
import Alert from '../../components/Alert';
import { User, FileText, ArrowLeft, Award, Calendar, CheckCircle2 } from 'lucide-react';

export default function CandidateProfile() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProfile();
  }, [id]);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const res = await api.getRecruiterCandidateProfile(id);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load candidate profile.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner-container">
        <div className="spinner"></div>
        <p>Loading candidate dossier...</p>
      </div>
    );
  }

  const { candidate, latest_resume, interviews } = data || {};

  return (
    <div className="page-container max-w-5xl">
      <div className="mb-4">
        <Link to="/recruiter/candidates" className="back-link flex items-center gap-1 text-sm text-muted">
          <ArrowLeft size={16} /> Back to Candidates List
        </Link>
      </div>

      <Alert type="error" message={error} />

      {/* Candidate Profile Header Card */}
      <div className="profile-hero-card">
        <div className="profile-avatar">
          <User size={36} />
        </div>
        <div>
          <h2>{candidate?.name}</h2>
          <p className="text-muted">{candidate?.email}</p>
          <div className="text-xs text-gray-500 mt-1">
            Registered: {candidate?.created_at ? new Date(candidate.created_at).toLocaleDateString() : 'N/A'}
          </div>
        </div>
      </div>

      {/* Resume Section */}
      <div className="section-card mt-6">
        <div className="section-header">
          <h3>
            <FileText size={18} className="inline mr-2 text-blue-600" />
            Resume Context
          </h3>
          {latest_resume && (
            <span className="text-xs text-muted">
              Uploaded on {new Date(latest_resume.uploaded_at).toLocaleString()}
            </span>
          )}
        </div>

        {latest_resume ? (
          <div>
            <div className="mb-2 text-sm font-semibold text-gray-700">
              File: {latest_resume.file_name}
            </div>
            <div className="extracted-text-preview max-h-64">
              <pre>{latest_resume.extracted_text}</pre>
            </div>
          </div>
        ) : (
          <p className="text-muted text-sm">No resume uploaded by this candidate yet.</p>
        )}
      </div>

      {/* Interviews Table */}
      <div className="section-card mt-6">
        <div className="section-header">
          <h3>Interview Assessments for Your Jobs</h3>
        </div>

        {(!interviews || interviews.length === 0) ? (
          <p className="text-muted text-sm">No interviews recorded for this candidate yet.</p>
        ) : (
          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Job Title</th>
                  <th>Status</th>
                  <th>Overall Score</th>
                  <th>Date</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {interviews.map((item) => (
                  <tr key={item.id}>
                    <td className="font-semibold">{item.job?.title || `Job #${item.job_id}`}</td>
                    <td>
                      <span className={`status-pill status-${item.status}`}>
                        {item.status === 'completed' ? 'Completed' : 'In Progress'}
                      </span>
                    </td>
                    <td>
                      {item.overall_score !== null ? (
                        <span className="score-badge">{item.overall_score.toFixed(1)} / 10</span>
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
                        <span className="text-xs text-muted">In Progress</span>
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
