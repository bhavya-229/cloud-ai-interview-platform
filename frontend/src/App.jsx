import React from 'react';
import { Routes, Route, Navigate, Link } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';

// Auth Pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';

// Candidate Pages
import CandidateDashboard from './pages/candidate/CandidateDashboard';
import ResumeUpload from './pages/candidate/ResumeUpload';
import AvailableJobs from './pages/candidate/AvailableJobs';
import InterviewSession from './pages/candidate/InterviewSession';
import InterviewResults from './pages/candidate/InterviewResults';

// Recruiter Pages
import RecruiterDashboard from './pages/recruiter/RecruiterDashboard';
import JobManagement from './pages/recruiter/JobManagement';
import CandidateList from './pages/recruiter/CandidateList';
import CandidateProfile from './pages/recruiter/CandidateProfile';
import RecruiterInterviewReport from './pages/recruiter/RecruiterInterviewReport';

import { Cpu, ArrowRight, ShieldCheck, Sparkles, FileText, CheckCircle2 } from 'lucide-react';

function HomeLanding() {
  const { isAuthenticated, role } = useAuth();

  if (isAuthenticated) {
    return <Navigate to={role === 'recruiter' ? '/recruiter/dashboard' : '/candidate/dashboard'} replace />;
  }

  return (
    <div className="landing-container page-container max-w-4xl text-center">
      <div className="mt-8 mb-6">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold mb-4 border border-blue-200">
          <Sparkles size={14} /> Cloud & Local AI Interview Platform
        </div>
        <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl mb-4">
          Next-Generation Technical Interviews, Powered by AI
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-8">
          Adaptive interview evaluations tailored to candidate resumes and recruiter job requirements. Built with modular cloud-ready architecture.
        </p>
        <div className="flex justify-center gap-4">
          <Link to="/register" className="btn-primary text-base px-6 py-3">
            Get Started Free <ArrowRight size={18} />
          </Link>
          <Link to="/login" className="btn-secondary text-base px-6 py-3">
            Sign In
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 text-left">
        <div className="card-box">
          <div className="stat-icon-wrapper blue mb-3">
            <FileText size={22} />
          </div>
          <h3 className="font-bold text-lg mb-2">Resume Context Extraction</h3>
          <p className="text-muted text-sm">
            Parses candidate PDF resumes locally and incorporates background into customized questions.
          </p>
        </div>

        <div className="card-box">
          <div className="stat-icon-wrapper purple mb-3">
            <Cpu size={22} />
          </div>
          <h3 className="font-bold text-lg mb-2">Adaptive AI Interviewer</h3>
          <p className="text-muted text-sm">
            Generates intelligent follow-up questions dynamically adjusting to previous answers and scores.
          </p>
        </div>

        <div className="card-box">
          <div className="stat-icon-wrapper green mb-3">
            <ShieldCheck size={22} />
          </div>
          <h3 className="font-bold text-lg mb-2">Hiring Assessment Dossier</h3>
          <p className="text-muted text-sm">
            Instant structured feedback reports highlighting strengths, weaknesses, and hiring recommendations.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <div className="app-layout">
      <Navbar />
      <main className="main-content">
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<HomeLanding />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Candidate Protected Routes */}
          <Route
            path="/candidate/dashboard"
            element={
              <ProtectedRoute allowedRole="candidate">
                <CandidateDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/resume"
            element={
              <ProtectedRoute allowedRole="candidate">
                <ResumeUpload />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/jobs"
            element={
              <ProtectedRoute allowedRole="candidate">
                <AvailableJobs />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/interview/:id"
            element={
              <ProtectedRoute allowedRole="candidate">
                <InterviewSession />
              </ProtectedRoute>
            }
          />
          <Route
            path="/candidate/interview/:id/results"
            element={
              <ProtectedRoute allowedRole="candidate">
                <InterviewResults />
              </ProtectedRoute>
            }
          />

          {/* Recruiter Protected Routes */}
          <Route
            path="/recruiter/dashboard"
            element={
              <ProtectedRoute allowedRole="recruiter">
                <RecruiterDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/recruiter/jobs"
            element={
              <ProtectedRoute allowedRole="recruiter">
                <JobManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="/recruiter/candidates"
            element={
              <ProtectedRoute allowedRole="recruiter">
                <CandidateList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/recruiter/candidates/:id"
            element={
              <ProtectedRoute allowedRole="recruiter">
                <CandidateProfile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/recruiter/interviews/:id/report"
            element={
              <ProtectedRoute allowedRole="recruiter">
                <RecruiterInterviewReport />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
