import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Cpu, LogOut, Briefcase, FileText, LayoutDashboard, Users } from 'lucide-react';

export default function Navbar() {
  const { user, isAuthenticated, role, logout } = useAuth();
  const navigate = useNavigate();
  const [platformMode, setPlatformMode] = React.useState('AWS Cloud');

  React.useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        if (data.storage === 's3' || data.database?.includes('rds')) {
          setPlatformMode('AWS Cloud');
        } else {
          setPlatformMode('Local Mode');
        }
      })
      .catch(() => setPlatformMode('AWS Cloud'));
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="brand-logo">
          <Cpu className="brand-icon" />
          <span className="brand-text">AI Interview Platform</span>
          <span className={platformMode === 'AWS Cloud' ? 'badge-cloud' : 'badge-local'}>
            {platformMode}
          </span>
        </Link>

        <div className="nav-links">
          {isAuthenticated ? (
            <>
              {role === 'candidate' && (
                <>
                  <Link to="/candidate/dashboard" className="nav-link">
                    <LayoutDashboard size={16} /> Dashboard
                  </Link>
                  <Link to="/candidate/resume" className="nav-link">
                    <FileText size={16} /> Resume
                  </Link>
                  <Link to="/candidate/jobs" className="nav-link">
                    <Briefcase size={16} /> Available Jobs
                  </Link>
                </>
              )}

              {role === 'recruiter' && (
                <>
                  <Link to="/recruiter/dashboard" className="nav-link">
                    <LayoutDashboard size={16} /> Dashboard
                  </Link>
                  <Link to="/recruiter/jobs" className="nav-link">
                    <Briefcase size={16} /> Manage Jobs
                  </Link>
                  <Link to="/recruiter/candidates" className="nav-link">
                    <Users size={16} /> Candidates
                  </Link>
                </>
              )}

              <div className="user-profile-badge">
                <span className="user-role-tag">{role}</span>
                <span className="user-name">{user?.name}</span>
                <button onClick={handleLogout} className="btn-logout" title="Sign Out">
                  <LogOut size={16} />
                </button>
              </div>
            </>
          ) : (
            <div className="auth-nav-buttons">
              <Link to="/login" className="btn-secondary">Log In</Link>
              <Link to="/register" className="btn-primary">Register</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
