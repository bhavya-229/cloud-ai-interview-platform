import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';
import Alert from '../../components/Alert';
import { Users, FileText, CheckCircle2, Award, ArrowRight } from 'lucide-react';

export default function CandidateList() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchCandidates();
  }, []);

  const fetchCandidates = async () => {
    try {
      setLoading(true);
      const data = await api.getRecruiterCandidates();
      setCandidates(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch candidate pool.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner-container">
        <div className="spinner"></div>
        <p>Loading candidate roster...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2>Candidate Pool</h2>
          <p className="subtitle">Candidates who have undertaken AI technical interviews for your job postings</p>
        </div>
      </div>

      <Alert type="error" message={error} />

      {candidates.length === 0 ? (
        <div className="empty-state">
          <Users size={40} className="text-gray-400 mb-2" />
          <p>No candidates have taken interviews for your postings yet.</p>
        </div>
      ) : (
        <div className="section-card">
          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Candidate Name</th>
                  <th>Email</th>
                  <th>Resume Status</th>
                  <th>Interviews Taken</th>
                  <th>Completed</th>
                  <th>Highest Score</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((item) => (
                  <tr key={item.candidate.id}>
                    <td className="font-semibold">{item.candidate.name}</td>
                    <td className="text-muted">{item.candidate.email}</td>
                    <td>
                      {item.latest_resume ? (
                        <span className="badge-pill bg-green-100 text-green-800 flex items-center gap-1 w-fit">
                          <CheckCircle2 size={13} /> {item.latest_resume.file_name}
                        </span>
                      ) : (
                        <span className="badge-pill bg-gray-100 text-gray-600">None</span>
                      )}
                    </td>
                    <td>{item.interviews_count}</td>
                    <td>{item.completed_count}</td>
                    <td>
                      {item.highest_score !== null ? (
                        <span className="score-badge">{item.highest_score.toFixed(1)} / 10</span>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td>
                      <Link to={`/recruiter/candidates/${item.candidate.id}`} className="btn-sm btn-outline flex items-center gap-1 w-fit">
                        View Profile <ArrowRight size={13} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
