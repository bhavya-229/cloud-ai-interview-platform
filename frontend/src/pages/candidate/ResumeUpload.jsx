import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import Alert from '../../components/Alert';
import { UploadCloud, FileText, CheckCircle2, AlertCircle } from 'lucide-react';

export default function ResumeUpload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [currentResume, setCurrentResume] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLatestResume();
  }, []);

  const fetchLatestResume = async () => {
    try {
      setLoading(false);
      const res = await api.getLatestResume();
      setCurrentResume(res);
    } catch {
      // 404 is expected if no resume uploaded yet
      setCurrentResume(null);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        setError('Only PDF files are supported.');
        setSelectedFile(null);
        return;
      }
      setError('');
      setSelectedFile(file);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a PDF file first.');
      return;
    }

    setUploading(true);
    setError('');
    setMessage('');

    try {
      const res = await api.uploadResume(selectedFile);
      setCurrentResume(res);
      setSelectedFile(null);
      setMessage('Resume uploaded and text extracted successfully!');
    } catch (err) {
      setError(err.message || 'Failed to process resume.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page-container max-w-4xl">
      <div className="page-header">
        <div>
          <h2>Resume Management</h2>
          <p className="subtitle">Upload your PDF resume so the AI interviewer can personalize questions</p>
        </div>
      </div>

      <Alert type="error" message={error} />
      <Alert type="success" message={message} />

      <div className="card-box upload-box">
        <form onSubmit={handleUpload}>
          <div className="file-drop-zone">
            <UploadCloud size={48} className="upload-icon" />
            <p className="upload-instructions">
              <strong>Click to browse</strong> or drag & drop your PDF resume here
            </p>
            <p className="upload-subtext">Supported format: PDF (Max size 10MB)</p>
            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="file-input-hidden"
              id="resume-file"
            />
            <label htmlFor="resume-file" className="btn-secondary mt-3">
              Browse Files
            </label>
            {selectedFile && (
              <div className="selected-file-pill">
                <FileText size={16} />
                <span>{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
              </div>
            )}
          </div>

          <div className="mt-4 flex justify-end">
            <button
              type="submit"
              className="btn-primary"
              disabled={!selectedFile || uploading}
            >
              {uploading ? 'Extracting Text & Saving...' : 'Upload & Process Resume'}
            </button>
          </div>
        </form>
      </div>

      {currentResume && (
        <div className="card-box mt-6">
          <div className="flex items-center justify-between border-b pb-3 mb-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={20} className="text-green-600" />
              <h3 className="text-lg font-semibold">Active Resume: {currentResume.file_name}</h3>
            </div>
            <span className="text-sm text-muted">
              Uploaded on {new Date(currentResume.uploaded_at).toLocaleString()}
            </span>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2">
              Extracted Resume Text (Context for AI)
            </h4>
            <div className="extracted-text-preview">
              <pre>{currentResume.extracted_text}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
