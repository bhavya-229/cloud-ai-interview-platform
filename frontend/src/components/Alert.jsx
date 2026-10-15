import React from 'react';
import { AlertCircle, CheckCircle, Info } from 'lucide-react';

export default function Alert({ type = 'error', message }) {
  if (!message) return null;

  const icons = {
    error: <AlertCircle className="alert-icon" size={18} />,
    success: <CheckCircle className="alert-icon" size={18} />,
    info: <Info className="alert-icon" size={18} />
  };

  return (
    <div className={`alert-box alert-${type}`}>
      {icons[type]}
      <span className="alert-text">{message}</span>
    </div>
  );
}
