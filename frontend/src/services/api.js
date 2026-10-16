const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  const headers = { ...options.headers };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // If body is not FormData, default to application/json
  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.dispatchEvent(new Event('auth:unauthorized'));
  }

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg = data.detail || (typeof data === 'string' ? data : 'An unexpected error occurred.');
    throw new Error(errorMsg);
  }

  return data;
}

export const api = {
  // Auth
  login: (email, password) => request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  }),
  register: (name, email, password, role) => request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password, role })
  }),
  getProfile: () => request('/auth/me'),

  // Jobs
  getJobs: () => request('/jobs'),
  getJob: (id) => request(`/jobs/${id}`),
  createJob: (jobData) => request('/jobs', {
    method: 'POST',
    body: JSON.stringify(jobData)
  }),
  updateJob: (id, jobData) => request(`/jobs/${id}`, {
    method: 'PUT',
    body: JSON.stringify(jobData)
  }),
  deleteJob: (id) => request(`/jobs/${id}`, {
    method: 'DELETE'
  }),

  // Resumes
  uploadResume: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/resumes/upload', {
      method: 'POST',
      body: formData
    });
  },
  getLatestResume: () => request('/resumes/latest'),
  getResume: (id) => request(`/resumes/${id}`),

  // Interviews
  startInterview: (jobId) => request('/interviews', {
    method: 'POST',
    body: JSON.stringify({ job_id: jobId })
  }),
  getInterview: (id) => request(`/interviews/${id}`),
  submitAnswer: (interviewId, questionId, answerText) => request(`/interviews/${interviewId}/answer`, {
    method: 'POST',
    body: JSON.stringify({ question_id: questionId, answer_text: answerText })
  }),
  getInterviewResults: (id) => request(`/interviews/${id}/results`),

  // Candidate
  getCandidateDashboard: () => request('/candidates/dashboard'),
  getCandidateInterviews: () => request('/candidates/interviews'),

  // Recruiter
  getRecruiterDashboard: () => request('/recruiters/dashboard'),
  getRecruiterInterviews: () => request('/recruiters/interviews'),
  getRecruiterCandidates: () => request('/recruiters/candidates'),
  getRecruiterCandidateProfile: (candidateId) => request(`/recruiters/candidates/${candidateId}`)
};
