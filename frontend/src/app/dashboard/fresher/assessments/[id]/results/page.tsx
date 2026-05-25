"use client";

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api-service';
import { useAuth } from '@/lib/auth-context';

/** Safely convert any value to a displayable string (handles objects from LLM output). */
function toDisplayString(val: unknown): string {
  if (val === null || val === undefined) return '';
  if (typeof val === 'string') return val;
  if (typeof val === 'object') {
    // Handle common LLM patterns like {area: "...", "specific topic": "..."}
    const obj = val as Record<string, unknown>;
    if (obj.area && obj['specific topic']) return `${obj.area}: ${obj['specific topic']}`;
    if (obj.area) return String(obj.area);
    return JSON.stringify(val);
  }
  return String(val);
}

interface WorkflowStatus {
  submission_id: string;
  status: string;
  score: number;
  max_score: number;
  pass_status: string;
  feedback: {
    overall_comment: string;
    strengths: string[];
    weaknesses: string[];
    suggestions: string[];
    missing_points?: string[];
    errors?: string[];
    improvements?: string[];
    risk_level: string;
    risk_factors?: string[];
    test_score?: number;
    style_score?: number;
    rubric_scores?: Record<string, number>;
    accuracy_score?: number;
  };
  test_results?: Array<{
    id: string;
    name: string;
    passed: boolean;
    expected: string;
    actual: string;
    error?: string;
    points: number;
  }>;
  assessment_title?: string;
  submitted_at?: string;
  graded_at?: string;
}

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { token, isLoading: authLoading } = useAuth();
  const assessmentId = params.id as string;
  const traceId = searchParams.get('trace_id');

  const [result, setResult] = useState<WorkflowStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Use a ref (not state) so poll count changes never re-trigger the effect
  const pollingCountRef = useRef(0);

  useEffect(() => {
    console.log(`[RESULTS] Page loaded, traceId=${traceId}, assessmentId=${assessmentId}`);
    // Reset poll counter whenever the key deps change (new trace or new token)
    pollingCountRef.current = 0;

    if (!traceId) {
      console.log(`[RESULTS] No trace ID provided, fetching latest result for assessment=${assessmentId}`);

      const fetchLatest = async () => {
        if (!token) return;

        try {
          const response = await api.assessment.getLatestResult(assessmentId, token);

          if (response.error || !response.data) {
            console.log(`[RESULTS] No latest result found:`, response.error);
            setError('No completed attempts found for this assessment.');
            setLoading(false);
            return;
          }

          const resultData = response.data as any;
          console.log(`[RESULTS] Got latest result:`, resultData);

          setResult({
            ...resultData,
            submission_id: resultData.submission_id || '',
            status: resultData.status || 'completed',
            score: resultData.score || 0,
            max_score: resultData.max_score || 100,
            pass_status: resultData.pass_status || 'pending',
            feedback: resultData.feedback || {
              overall_comment: '',
              strengths: [],
              weaknesses: [],
              suggestions: [],
              risk_level: 'low'
            }
          });
          setLoading(false);
        } catch (err) {
          console.error("Error fetching latest:", err);
          setError('Failed to load assessment results.');
          setLoading(false);
        }
      };

      fetchLatest();
      return;
    }

    // cancelled flag prevents state updates after the effect is cleaned up
    let cancelled = false;

    const pollStatus = async () => {
      if (cancelled) return;
      if (authLoading) return;

      if (!token) {
        router.push('/login');
        return;
      }

      console.log(`[RESULTS] Polling status for trace_id=${traceId} (attempt ${pollingCountRef.current + 1})`);
      const response = await api.workflow.getStatus(traceId, token);

      if (cancelled) return;

      if (response.error) {
        console.log(`[RESULTS] Status API error:`, response.error);
        setError(response.error);
        setLoading(false);
        return;
      }

      if (response.data) {
        const data = response.data as any;
        console.log(`[RESULTS] Got workflow status:`, data);

        // Handle both direct data and nested state
        const resultData = data.state || data;

        if (data.status === 'completed' || data.status === 'graded' || resultData.pass_status) {
          setResult({
            ...resultData,
            status: data.status || resultData.status,
            submission_id: resultData.submission_id,
            score: resultData.score || 0,
            max_score: resultData.max_score || 100,
            pass_status: resultData.pass_status || 'pending',
            feedback: resultData.feedback || {
              overall_comment: '',
              strengths: [],
              weaknesses: [],
              suggestions: [],
              missing_points: [],
              errors: [],
              improvements: [],
              risk_level: 'low',
            },
            test_results: resultData.test_results || [],
          });
          setLoading(false);
        } else if (data.status === 'failed') {
          setError('Assessment grading failed. Please contact support.');
          setLoading(false);
        } else {
          // Continue polling — increment ref (not state) so the effect doesn't re-fire
          pollingCountRef.current += 1;
          if (pollingCountRef.current < 30) {
            setTimeout(pollStatus, 2000);
          } else {
            setError('Grading is taking longer than expected. Please check back later.');
            setLoading(false);
          }
        }
      }
    };

    pollStatus();

    // Cleanup: mark as cancelled so no stale updates arrive after unmount or dep change
    return () => { cancelled = true; };
  // pollingCountRef is intentionally excluded — it's a ref, not reactive state
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [traceId, router, token, authLoading]);

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'low':
        return 'text-green-600 bg-green-100';
      case 'medium':
        return 'text-orange-600 bg-orange-100';
      case 'high':
        return 'text-red-600 bg-red-100';
      case 'critical':
        return 'text-red-800 bg-red-200';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getScoreColor = (score: number, maxScore: number) => {
    const percentage = (score / maxScore) * 100;
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-blue-600';
    if (percentage >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-50">
        <div className="text-center">
          <div className="relative">
            <div className="animate-spin rounded-full h-20 w-20 border-b-4 border-indigo-600 mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl">🤖</span>
            </div>
          </div>
          <h2 className="mt-6 text-2xl font-bold text-gray-800">AI Agent Evaluating...</h2>
          <p className="mt-2 text-gray-600">
            The Assessment Agent is analyzing your submission
          </p>
          <div className="mt-4 flex items-center justify-center gap-2">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error Loading Results</h2>
          <p className="text-gray-600 mb-6">{error || 'Results not found'}</p>
          <div className="flex gap-3">
            <button
              onClick={() => router.push(`/dashboard/fresher/assessments/${assessmentId}/quiz`)}
              className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition"
            >
              Take Quiz
            </button>
            <button
              onClick={() => router.push('/dashboard/fresher')}
              className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition"
            >
              Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  const passed = result.pass_status === 'pass';
  const scorePercentage = (result.score / result.max_score) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Header Card */}
        <div className={`rounded-lg shadow-lg p-8 mb-6 ${passed ? 'bg-gradient-to-r from-green-500 to-green-600' : 'bg-gradient-to-r from-orange-500 to-orange-600'}`}>
          <div className="text-center text-white">
            <div className="text-6xl mb-4">{passed ? '🎉' : '📚'}</div>
            <h1 className="text-4xl font-bold mb-2">
              {passed ? 'Congratulations!' : 'Keep Learning!'}
            </h1>
            <p className="text-xl opacity-90">
              {passed ? 'You passed the assessment!' : 'Review feedback and try again'}
            </p>

            <div className="mt-8 flex justify-center gap-4">
              <button
                onClick={() => router.push('/dashboard/fresher')}
                className="px-6 py-2 bg-white/20 hover:bg-white/30 text-white font-semibold rounded-lg transition-colors border border-white/30 backdrop-blur-sm"
              >
                Dashboard
              </button>
              <button
                onClick={() => router.push(`/dashboard/fresher/assessments/${assessmentId}/quiz`)}
                className="px-6 py-2 bg-white text-indigo-600 font-bold rounded-lg shadow-lg hover:bg-gray-50 transition-all transform hover:scale-105 active:scale-95"
              >
                {passed ? 'Retake Assessment' : 'Try Again'}
              </button>
            </div>
          </div>
        </div>

        {/* Score Card */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
            <span>📊</span> Your Score
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <div className={`text-5xl font-bold mb-2 ${getScoreColor(result.score, result.max_score)}`}>
                {result.score.toFixed(1)}
              </div>
              <div className="text-gray-600">Out of {result.max_score}</div>
              <div className="mt-2 text-sm text-gray-500">
                {scorePercentage.toFixed(1)}%
              </div>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <div className={`text-3xl font-bold mb-2 ${passed ? 'text-green-600' : 'text-orange-600'}`}>
                {passed ? '✓ PASSED' : '✗ NOT PASSED'}
              </div>
              <div className="text-gray-600">Status</div>
              <div className="mt-2 text-sm text-gray-500">
                Pass Score: {result.max_score * 0.6}
              </div>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <div className={`inline-block px-4 py-2 rounded-full font-semibold ${getRiskColor(result.feedback.risk_level)}`}>
                {result.feedback.risk_level?.toUpperCase() || 'LOW'} RISK
              </div>
              <div className="text-gray-600 mt-2">Performance Level</div>
            </div>
          </div>

          {/* Detailed Scores for Code Challenges */}
          {result.feedback.test_score !== undefined && result.feedback.test_score !== null && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex justify-between items-center">
                  <span className="text-gray-700 font-medium">Test Cases Score</span>
                  <span className="text-xl font-bold text-blue-600">
                    {typeof result.feedback.test_score === 'number' ? result.feedback.test_score.toFixed(1) : Number(result.feedback.test_score).toFixed(1)}%
                  </span>
                </div>
                <div className="mt-2 w-full bg-blue-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${typeof result.feedback.test_score === 'number' ? result.feedback.test_score : Number(result.feedback.test_score)}%` }}
                  ></div>
                </div>
              </div>

              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <div className="flex justify-between items-center">
                  <span className="text-gray-700 font-medium">Code Quality Score</span>
                  <span className="text-xl font-bold text-purple-600">
                    {typeof result.feedback.style_score === 'number' ? result.feedback.style_score.toFixed(1) : (result.feedback.style_score ? Number(result.feedback.style_score).toFixed(1) : '0.0')}%
                  </span>
                </div>
                <div className="mt-2 w-full bg-purple-200 rounded-full h-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full"
                    style={{ width: `${typeof result.feedback.style_score === 'number' ? result.feedback.style_score : (result.feedback.style_score ? Number(result.feedback.style_score) : 0)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          )}

          {/* Accuracy Score for Quizzes */}
          {result.feedback.accuracy_score !== undefined && result.feedback.accuracy_score !== null && (
            <div className="mt-6">
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex justify-between items-center">
                  <span className="text-gray-700 font-medium">Accuracy</span>
                  <span className="text-xl font-bold text-blue-600">
                    {typeof result.feedback.accuracy_score === 'number' ? result.feedback.accuracy_score.toFixed(1) : Number(result.feedback.accuracy_score).toFixed(1)}%
                  </span>
                </div>
                <div className="mt-2 w-full bg-blue-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${typeof result.feedback.accuracy_score === 'number' ? result.feedback.accuracy_score : Number(result.feedback.accuracy_score)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* AI Feedback Card */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
            <span>🤖</span> AI Agent Feedback
          </h2>

          {/* Overall Comment */}
          <div className="mb-6 p-6 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg">
            <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
              <span>💬</span> Overall Assessment
            </h3>
            <p className="text-gray-700 leading-relaxed">
              {toDisplayString(result.feedback.overall_comment)}
            </p>
          </div>

          {/* Strengths */}
          {result.feedback.strengths && result.feedback.strengths.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span>💪</span> Strengths
              </h3>
              <ul className="space-y-2">
                {result.feedback.strengths.map((strength, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                    <span className="text-green-600 text-xl">✓</span>
                    <span className="text-gray-700 flex-1">{toDisplayString(strength)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Weaknesses */}
          {result.feedback.weaknesses && result.feedback.weaknesses.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span>📉</span> Areas for Improvement
              </h3>
              <ul className="space-y-2">
                {result.feedback.weaknesses.map((weakness, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg">
                    <span className="text-orange-600 text-xl">⚠</span>
                    <span className="text-gray-700 flex-1">{toDisplayString(weakness)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Points */}
          {result.feedback.missing_points && result.feedback.missing_points.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span>🧩</span> Missing Points
              </h3>
              <ul className="space-y-2">
                {result.feedback.missing_points.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg">
                    <span className="text-yellow-700 text-xl">•</span>
                    <span className="text-gray-700 flex-1">{toDisplayString(item)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Errors Explained */}
          {result.feedback.errors && result.feedback.errors.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span>🧯</span> Errors Explained
              </h3>
              <ul className="space-y-2">
                {result.feedback.errors.map((err, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
                    <span className="text-red-600 text-xl">!</span>
                    <span className="text-gray-700 flex-1">{toDisplayString(err)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggestions */}
          {result.feedback.suggestions && result.feedback.suggestions.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span>💡</span> Recommendations
              </h3>
              <ul className="space-y-2">
                {result.feedback.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                    <span className="text-blue-600 text-xl">→</span>
                    <span className="text-gray-700 flex-1">{toDisplayString(suggestion)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Improvements */}
          {result.feedback.improvements && result.feedback.improvements.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span>🛠️</span> Improvements to Try
              </h3>
              <ul className="space-y-2">
                {result.feedback.improvements.map((improvement, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-indigo-50 rounded-lg">
                    <span className="text-indigo-600 text-xl">→</span>
                    <span className="text-gray-700 flex-1">{toDisplayString(improvement)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Risk Factors */}
          {result.feedback.risk_factors && result.feedback.risk_factors.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span>⚡</span> Risk Factors
              </h3>
              <ul className="space-y-2">
                {result.feedback.risk_factors.map((factor, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-red-50 rounded-lg">
                    <span className="text-red-600 text-xl">!</span>
                    <span className="text-gray-700 flex-1">{toDisplayString(factor)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Test Results for Code Challenges */}
        {result.test_results && result.test_results.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-8 mb-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
              <span>🧪</span> Test Case Results
            </h2>

            <div className="space-y-3">
              {result.test_results.map((test, idx) => (
                <div
                  key={test.id}
                  className={`p-4 rounded-lg border-l-4 ${test.passed
                    ? 'bg-green-50 border-green-500'
                    : 'bg-red-50 border-red-500'
                    }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className={`text-2xl ${test.passed ? 'text-green-600' : 'text-red-600'}`}>
                        {test.passed ? '✓' : '✗'}
                      </span>
                      <div>
                        <h4 className="font-semibold text-gray-800">{test.name}</h4>
                        <p className="text-sm text-gray-600">{test.points} points</p>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${test.passed
                      ? 'bg-green-200 text-green-800'
                      : 'bg-red-200 text-red-800'
                      }`}>
                      {test.passed ? 'PASSED' : 'FAILED'}
                    </span>
                  </div>

                  {!test.passed && (
                    <div className="mt-3 space-y-2 text-sm">
                      <div>
                        <span className="text-gray-600 font-medium">Expected:</span>
                        <pre className="mt-1 p-2 bg-white border border-gray-200 rounded text-gray-800 overflow-x-auto">
                          {test.expected}
                        </pre>
                      </div>
                      <div>
                        <span className="text-gray-600 font-medium">Got:</span>
                        <pre className="mt-1 p-2 bg-white border border-gray-200 rounded text-gray-800 overflow-x-auto">
                          {test.actual}
                        </pre>
                      </div>
                      {test.error && (
                        <div>
                          <span className="text-red-600 font-medium">Error:</span>
                          <pre className="mt-1 p-2 bg-white border border-red-200 rounded text-red-600 overflow-x-auto">
                            {test.error}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => router.push('/dashboard/fresher/assessments')}
            className="px-8 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition font-semibold"
          >
            Back to Assessments
          </button>
          <button
            onClick={() => router.push('/dashboard/fresher')}
            className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
