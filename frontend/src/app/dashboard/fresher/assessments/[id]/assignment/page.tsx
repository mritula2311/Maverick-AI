"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api-service';
import { AssessmentDetail } from '@/lib/types';
import { useAuth } from '@/lib/auth-context';

export default function AssignmentPage() {
  const params = useParams();
  const router = useRouter();
  const { token, isLoading: authLoading } = useAuth();
  const assessmentId = params.id as string;

  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [submission, setSubmission] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    const loadAssessment = async () => {
      if (authLoading) return; // Wait for auth to finish loading

      if (!token) {
        router.push('/login');
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const result = await api.assessment.get(assessmentId, token);

        if (result.error) {
          setError(result.error || "Failed to load assessment");
          setLoading(false);
          return;
        }

        if (result.data) {
          setAssessment(result.data as any);
          setTimeRemaining(result.data.time_limit_minutes * 60);
        } else {
          setError("No assessment data received");
        }
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
        setLoading(false);
      }
    };

    loadAssessment();
  }, [assessmentId, router, token, authLoading]);

  // Timer countdown
  useEffect(() => {
    if (timeRemaining === null || timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev === null || prev <= 1) {
          handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining]);

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours > 0 ? `${hours}:` : ''}${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Check file size (max 10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleSubmit = async () => {
    if (!showConfirmation) {
      if (!submission.trim() && !file) {
        alert('Please provide your assignment response or upload a file.');
        return;
      }
      setShowConfirmation(true);
      return;
    }

    setSubmitting(true);

    if (!token) {
      router.push('/login');
      return;
    }

    // Submit via workflow API
    const result = await api.workflow.submit(
      {
        assessment_id: assessmentId,
        submission_type: 'assignment',
        code: submission,
        language: 'text',
      },
      token
    );

    if (result.error) {
      setError(result.error);
      setSubmitting(false);
      setShowConfirmation(false);
      return;
    }

    if (result.data) {
      // Redirect to results page with trace_id for status polling
      router.push(`/dashboard/fresher/assessments/${assessmentId}/results?trace_id=${result.data.trace_id}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading assignment...</p>
        </div>
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error Loading Assignment</h2>
          <p className="text-gray-600 mb-6">{error || 'Assignment not found'}</p>
          <button
            onClick={() => router.push('/dashboard/fresher/assessments')}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            Back to Assessments
          </button>
        </div>
      </div>
    );
  }

  const wordCount = submission.trim().split(/\s+/).filter(Boolean).length;
  const charCount = submission.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Header Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-3xl">📄</span>
                <h1 className="text-2xl font-bold text-gray-900">{assessment.title}</h1>
              </div>
              <p className="text-gray-600 mt-2">{assessment.description}</p>
            </div>
            {timeRemaining !== null && (
              <div className={`text-xl font-mono font-bold ${timeRemaining < 600 ? 'text-red-600 animate-pulse' : 'text-gray-800'}`}>
                ⏱️ {formatTime(timeRemaining)}
              </div>
            )}
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-2 text-gray-600">
              <span>📊</span>
              <span>{assessment.max_score} points</span>
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <span>🎯</span>
              <span>Pass: {assessment.passing_score} points</span>
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <span>🔄</span>
              <span>Max {assessment.max_attempts} attempts</span>
            </div>
          </div>
        </div>

        {/* Instructions Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span>📋</span> Assignment Instructions
          </h2>
          <div className="prose max-w-none">
            <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
              {assessment.instructions || assessment.description}
            </p>
          </div>

          {/* Guidelines */}
          <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg">
            <h3 className="font-semibold text-blue-900 mb-2">Guidelines:</h3>
            <ul className="text-blue-800 text-sm space-y-1">
              <li>• Write a clear, well-structured response</li>
              <li>• Support your arguments with examples</li>
              <li>• Proofread before submitting</li>
              <li>• You can upload a document or type directly</li>
            </ul>
          </div>
        </div>

        {/* Submission Area */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span>✍️</span> Your Submission
          </h2>

          {/* File Upload Option */}
          <div className="mb-6">
            <label className="block text-gray-700 font-medium mb-2">
              Upload Document (Optional)
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition">
              <input
                type="file"
                onChange={handleFileUpload}
                accept=".pdf,.doc,.docx,.txt"
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <div className="text-5xl mb-2">📎</div>
                {file ? (
                  <div className="text-green-600 font-semibold">
                    ✓ {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </div>
                ) : (
                  <>
                    <div className="text-gray-600 mb-1">
                      Click to upload a file
                    </div>
                    <div className="text-sm text-gray-500">
                      PDF, DOC, DOCX, TXT (Max 10MB)
                    </div>
                  </>
                )}
              </label>
            </div>
          </div>

          <div className="relative">
            <div className="mb-2 flex justify-between items-center">
              <label className="block text-gray-700 font-medium">
                Written Response
              </label>
              <div className="text-sm text-gray-500">
                {wordCount} words | {charCount} characters
              </div>
            </div>
            <textarea
              value={submission}
              onChange={(e) => setSubmission(e.target.value)}
              placeholder="Type your assignment response here..."
              className="w-full p-4 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition font-mono text-sm"
              rows={20}
            />
          </div>

          {/* Submission Stats */}
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-600">{wordCount}</div>
                <div className="text-xs text-gray-600">Words</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">{charCount}</div>
                <div className="text-xs text-gray-600">Characters</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {submission.trim().split('\n').filter(Boolean).length}
                </div>
                <div className="text-xs text-gray-600">Paragraphs</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-orange-600">
                  {Math.ceil(wordCount / 200)}
                </div>
                <div className="text-xs text-gray-600">Est. Minutes</div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={() => router.push('/dashboard/fresher/assessments')}
            className="flex-1 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition font-semibold"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || (!submission.trim() && !file)}
            className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Submitting...' : 'Submit Assignment'}
          </button>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Submit Assignment?</h3>
            <div className="text-gray-600 mb-6 space-y-2">
              <p>You are about to submit your assignment for AI evaluation.</p>
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm font-semibold text-blue-800">
                  📝 {wordCount} words written
                </p>
                {file && (
                  <p className="text-sm font-semibold text-blue-800 mt-1">
                    📎 File attached: {file.name}
                  </p>
                )}
              </div>
              <p className="text-sm">Once submitted, you cannot edit your response.</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirmation(false)}
                className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50"
              >
                {submitting ? 'Submitting...' : 'Confirm Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
