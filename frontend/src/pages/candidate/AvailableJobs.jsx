import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import Alert from '../../components/Alert';
import { Briefcase, Play, CheckCircle2, Tag, Calendar } from 'lucide-react';

export default function AvailableJobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [startingJobId, setStartingJobId] = useState(null);
  const [error, setError] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const res = await api.getJobs();
      setJobs(res);
    } catch (err) {
      setError(err.message || 'Failed to load jobs.');
    } finally {
      setLoading(false);
    }
  };

  const handleStartInterview = async (jobId) => {
    setStartingJobId(jobId);
    setError('');
    try {
      const interview = await api.startInterview(jobId);
      navigate(`/candidate/interview/${interview.id}`);
    } catch (err) {
      setError(err.message || 'Failed to start interview.');
      setStartingJobId(null);
    }
  };

  if (loading) {
    return <div className="loading-spinner-container"><div className="spinner"></div><p>Loading available positions...</p></div>;
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2>Available Job Openings</h2>
          <p className="subtitle">Select a position to initiate your adaptive AI technical interview</p>
        </div>
      </div>

      <Alert type="error" message={error} />

      {jobs.length === 0 ? (
        <div className="empty-state">
          <Briefcase size={40} className="text-gray-400 mb-2" />
          <p>No jobs have been posted by recruiters yet.</p>
        </div>
      ) : (
        <div className="jobs-grid">
          {jobs.map((job) => (
            <div key={job.id} className="job-card">
              <div className="job-card-header">
                <div>
                  <h3 className="job-title">{job.title}</h3>
                  <div className="job-meta">
                    <Calendar size={14} />
                    <span>Posted {new Date(job.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              <p className="job-description">{job.description}</p>

              <div className="job-skills-section">
                <span className="skills-heading">Required Skills:</span>
                <div className="skills-tags">
                  {job.required_skills.split(',').map((skill, idx) => (
                    <span key={idx} className="skill-tag">
                      <Tag size={12} /> {skill.trim()}
                    </span>
                  ))}
                </div>
              </div>

              <div className="job-card-footer">
                <button
                  className="btn-primary btn-block flex items-center justify-center gap-2"
                  onClick={() => handleStartInterview(job.id)}
                  disabled={startingJobId === job.id}
                >
                  <Play size={16} />
                  {startingJobId === job.id ? 'Generating Interview Questions...' : 'Start AI Interview'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
