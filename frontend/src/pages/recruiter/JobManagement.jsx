import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import Alert from '../../components/Alert';
import { PlusCircle, Edit3, Trash2, Tag, Calendar, X, Briefcase } from 'lucide-react';

export default function JobManagement() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form State
  const [showModal, setShowModal] = useState(false);
  const [editingJobId, setEditingJobId] = useState(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [requiredSkills, setRequiredSkills] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const res = await api.getJobs();
      setJobs(res);
    } catch (err) {
      setError(err.message || 'Failed to fetch job postings.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreateModal = () => {
    setEditingJobId(null);
    setTitle('');
    setDescription('');
    setRequiredSkills('');
    setShowModal(true);
    setError('');
  };

  const handleOpenEditModal = (job) => {
    setEditingJobId(job.id);
    setTitle(job.title);
    setDescription(job.description);
    setRequiredSkills(job.required_skills);
    setShowModal(true);
    setError('');
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingJobId(null);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess('');

    try {
      const payload = {
        title,
        description,
        required_skills: requiredSkills
      };

      if (editingJobId) {
        await api.updateJob(editingJobId, payload);
        setSuccess('Job posting updated successfully.');
      } else {
        await api.createJob(payload);
        setSuccess('New job posting created successfully.');
      }

      handleCloseModal();
      fetchJobs();
    } catch (err) {
      setError(err.message || 'Failed to save job posting.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteJob = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this job posting? Associated interviews will be affected.')) {
      return;
    }

    try {
      await api.deleteJob(jobId);
      setSuccess('Job posting deleted.');
      fetchJobs();
    } catch (err) {
      setError(err.message || 'Failed to delete job posting.');
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner-container">
        <div className="spinner"></div>
        <p>Loading jobs...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2>Job Postings Management</h2>
          <p className="subtitle">Create and configure job requirements for AI technical evaluations</p>
        </div>
        <button onClick={handleOpenCreateModal} className="btn-primary flex items-center gap-2">
          <PlusCircle size={18} /> Create New Job
        </button>
      </div>

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      {/* Jobs Grid */}
      {jobs.length === 0 ? (
        <div className="empty-state">
          <Briefcase size={40} className="text-gray-400 mb-2" />
          <p>You haven't posted any jobs yet.</p>
          <button onClick={handleOpenCreateModal} className="btn-primary mt-3">
            Post Your First Job
          </button>
        </div>
      ) : (
        <div className="jobs-grid">
          {jobs.map((job) => (
            <div key={job.id} className="job-card">
              <div className="job-card-header">
                <h3 className="job-title">{job.title}</h3>
                <div className="job-actions-toolbar">
                  <button onClick={() => handleOpenEditModal(job)} className="action-btn text-blue-600" title="Edit">
                    <Edit3 size={16} />
                  </button>
                  <button onClick={() => handleDeleteJob(job.id)} className="action-btn text-red-600" title="Delete">
                    <Trash2 size={16} />
                  </button>
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

              <div className="job-card-meta-footer">
                <Calendar size={14} /> Created {new Date(job.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal for Create / Edit */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3>{editingJobId ? 'Edit Job Posting' : 'Create New Job Posting'}</h3>
              <button onClick={handleCloseModal} className="modal-close-btn">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleFormSubmit} className="modal-form">
              <div className="form-group">
                <label htmlFor="title">Job Title</label>
                <input
                  id="title"
                  type="text"
                  required
                  placeholder="e.g. Senior Full-Stack Engineer"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="skills">Required Skills (comma-separated)</label>
                <input
                  id="skills"
                  type="text"
                  required
                  placeholder="e.g. Python, FastAPI, Docker, SQL, AWS Architecture"
                  value={requiredSkills}
                  onChange={(e) => setRequiredSkills(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="description">Job Description</label>
                <textarea
                  id="description"
                  rows={5}
                  required
                  placeholder="Describe key responsibilities and expectations for this technical position..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className="modal-footer">
                <button type="button" onClick={handleCloseModal} className="btn-secondary" disabled={submitting}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={submitting}>
                  {submitting ? 'Saving...' : (editingJobId ? 'Update Job' : 'Create Job')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
