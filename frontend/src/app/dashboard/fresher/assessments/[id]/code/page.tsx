"use client";

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api-service';
import { AssessmentDetail } from '@/lib/types';
import { useAuth } from '@/lib/auth-context';
import dynamic from 'next/dynamic';

// Dynamically import Monaco editor (client-side only)
const Editor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

export default function CodeSubmissionPage() {
  const params = useParams();
  const router = useRouter();
  const { token, isLoading: authLoading } = useAuth();
  const assessmentId = params.id as string;

  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [code, setCode] = useState<string>('');
  const [language, setLanguage] = useState<string>('python');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [testResults, setTestResults] = useState<any[]>([]);
  const [selectedTestCase, setSelectedTestCase] = useState<number>(0);
  const editorRef = useRef<any>(null);
  const handleSubmitRef = useRef<() => void>(() => {});

  // Load assessment data
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
          const assessmentData = result.data as any;
          setAssessment(assessmentData);
          setCode(assessmentData.starter_code || getDefaultCode(assessmentData.language || 'python'));
          setLanguage(assessmentData.language || 'python');
          setTimeRemaining(assessmentData.time_limit_minutes * 60);
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

  // Keep ref in sync so the timer can call the latest handleSubmit without a stale closure
  useEffect(() => { handleSubmitRef.current = handleSubmit; });

  // Timer countdown — chained timeouts so the interval is never recreated mid-tick
  useEffect(() => {
    if (timeRemaining === null || timeRemaining <= 0) return;

    const timer = setTimeout(() => {
      setTimeRemaining((prev) => {
        const next = (prev ?? 1) - 1;
        if (next <= 0) {
          setTimeout(() => handleSubmitRef.current(), 0);
          return 0;
        }
        return next;
      });
    }, 1000);

    return () => clearTimeout(timer);
  }, [timeRemaining]);

  const getDefaultCode = (lang: string) => {
    const templates: Record<string, string> = {
      python: '# Write your solution here\ndef solution():\n    pass\n',
      javascript: '// Write your solution here\nfunction solution() {\n    \n}\n',
      java: 'public class Solution {\n    public static void main(String[] args) {\n        // Write your solution here\n    }\n}\n',
      cpp: '#include <iostream>\nusing namespace std;\n\nint main() {\n    // Write your solution here\n    return 0;\n}\n',
    };
    return templates[lang] || templates.python;
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours > 0 ? `${hours}:` : ''}${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
    editor.focus();
  };

  const handleRunTests = async () => {
    if (!assessment) return;
    
    setRunning(true);
    setTestResults([]);
    
    // Simulate test execution (in real implementation, this would call backend)
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Mock results for visible test cases
    const mockResults = (assessment.test_cases || []).filter(tc => !tc.hidden).map((tc) => ({
      test_name: tc.name || tc.id || 'Test',
      passed: Math.random() > 0.3, // Random pass/fail for demo
      expected: tc.expected_output,
      actual: Math.random() > 0.3 ? tc.expected_output : "Different output",
      execution_time_ms: Math.floor(Math.random() * 100) + 10,
    }));
    
    setTestResults(mockResults);
    setRunning(false);
  };

  const handleSubmit = async () => {
    if (!showConfirmation) {
      setShowConfirmation(true);
      return;
    }

    if (!token) {
      router.push('/login');
      return;
    }

    setSubmitting(true);
    
    // Submit via workflow API
    const result = await api.workflow.submit(
      {
        assessment_id: assessmentId,
        submission_type: 'code',
        code,
        language,
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

  const handleReset = () => {
    if (assessment?.starter_code) {
      setCode(assessment.starter_code);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error Loading Assessment</h2>
          <p className="text-gray-600 mb-6">{error || 'Assessment not found'}</p>
          <button
            onClick={() => router.push('/dashboard/fresher')}
            className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const visibleTestCases = (assessment.test_cases || []).filter(tc => !tc.hidden);
  const passedTests = testResults.filter(r => r.passed).length;
  const totalTests = testResults.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{assessment.title}</h1>
            <p className="text-gray-600 text-sm mt-1">{language.toUpperCase()} - {assessment.max_score} points</p>
          </div>
          <div className="flex items-center gap-4">
            {timeRemaining !== null && (
              <div className={`text-xl font-mono font-bold ${timeRemaining < 300 ? 'text-red-600 animate-pulse' : 'text-gray-900'}`}>
                ⏱️ {formatTime(timeRemaining)}
              </div>
            )}
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition"
            >
              Reset Code
            </button>
            <button
              onClick={handleRunTests}
              disabled={running}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
            >
              {running ? 'Running...' : '▶ Run Tests'}
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-semibold disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : 'Submit Solution'}
            </button>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-80px)]">
        {/* Left Panel - Instructions & Test Cases */}
        <div className="w-1/3 bg-gray-800 border-r border-gray-700 overflow-y-auto">
          {/* Instructions */}
          <div className="p-6 border-b border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-3">Problem Description</h2>
            <div className="text-gray-300 whitespace-pre-wrap text-sm leading-relaxed">
              {assessment.description}
            </div>
            {assessment.instructions && (
              <div className="mt-4 p-4 bg-gray-900 rounded-lg">
                <h3 className="text-sm font-semibold text-blue-400 mb-2">Instructions</h3>
                <p className="text-gray-300 text-sm whitespace-pre-wrap">{assessment.instructions}</p>
              </div>
            )}
          </div>

          {/* Test Cases */}
          <div className="p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Test Cases</h2>
            <div className="space-y-3">
              {visibleTestCases.map((testCase, index) => (
                <button
                  key={testCase.id}
                  onClick={() => setSelectedTestCase(index)}
                  className={`
                    w-full text-left p-4 rounded-lg border transition
                    ${selectedTestCase === index
                      ? 'border-blue-500 bg-gray-900'
                      : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                    }
                  `}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-semibold text-white">{testCase.name}</span>
                    <span className="text-xs text-gray-400">{testCase.points} pts</span>
                  </div>
                  {testResults.length > 0 && testResults[index] && (
                    <div className={`text-xs font-semibold ${testResults[index].passed ? 'text-green-400' : 'text-red-400'}`}>
                      {testResults[index].passed ? '✓ PASSED' : '✗ FAILED'} ({testResults[index].execution_time_ms}ms)
                    </div>
                  )}
                </button>
              ))}
            </div>

            {/* Test Results Summary */}
            {testResults.length > 0 && (
              <div className="mt-6 p-4 bg-gray-900 rounded-lg">
                <h3 className="text-sm font-semibold text-white mb-2">Results</h3>
                <div className={`text-2xl font-bold ${passedTests === totalTests ? 'text-green-400' : 'text-orange-400'}`}>
                  {passedTests} / {totalTests} Passed
                </div>
                <div className="mt-2 w-full bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${passedTests === totalTests ? 'bg-green-500' : 'bg-orange-500'}`}
                    style={{ width: `${(passedTests / totalTests) * 100}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Selected Test Case Details */}
            {visibleTestCases.length > 0 && (
              <div className="mt-6 p-4 bg-gray-900 rounded-lg">
                <h3 className="text-sm font-semibold text-blue-400 mb-3">Test Case Details</h3>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-gray-400 block mb-1">Input:</span>
                    <pre className="bg-gray-800 p-2 rounded text-green-400 overflow-x-auto">
                      {JSON.stringify(visibleTestCases[selectedTestCase].input, null, 2)}
                    </pre>
                  </div>
                  <div>
                    <span className="text-gray-400 block mb-1">Expected Output:</span>
                    <pre className="bg-gray-800 p-2 rounded text-blue-400 overflow-x-auto">
                      {JSON.stringify(visibleTestCases[selectedTestCase].expected_output, null, 2)}
                    </pre>
                  </div>
                  {testResults.length > 0 && testResults[selectedTestCase] && (
                    <div>
                      <span className="text-gray-400 block mb-1">Actual Output:</span>
                      <pre className={`bg-gray-800 p-2 rounded overflow-x-auto ${testResults[selectedTestCase].passed ? 'text-green-400' : 'text-red-400'}`}>
                        {JSON.stringify(testResults[selectedTestCase].actual, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Code Editor */}
        <div className="flex-1 flex flex-col">
          {/* Editor Header */}
          <div className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-sm">Language:</span>
              <span className="text-white font-medium">{language.toUpperCase()}</span>
            </div>
            <div className="text-gray-400 text-xs">
              Lines: {code.split('\n').length} | Characters: {code.length}
            </div>
          </div>

          {/* Monaco Editor */}
          <div className="flex-1">
            <Editor
              height="100%"
              language={language}
              value={code}
              onChange={(value) => setCode(value || '')}
              onMount={handleEditorDidMount}
              theme="vs-dark"
              options={{
                minimap: { enabled: true },
                fontSize: 14,
                lineNumbers: 'on',
                roundedSelection: false,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 4,
                wordWrap: 'on',
                formatOnPaste: true,
                formatOnType: true,
              }}
            />
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6 border border-gray-700">
            <h3 className="text-xl font-bold text-white mb-4">Submit Solution?</h3>
            <div className="text-gray-300 mb-6 space-y-2">
              <p>Are you sure you want to submit your solution?</p>
              {testResults.length > 0 ? (
                <div className={`p-3 rounded-lg ${passedTests === totalTests ? 'bg-green-900/30 text-green-400' : 'bg-orange-900/30 text-orange-400'}`}>
                  Your code passed {passedTests} out of {totalTests} visible test cases.
                </div>
              ) : (
                <p className="text-orange-400 font-semibold">
                  Warning: You haven't run the tests yet!
                </p>
              )}
              <p className="text-sm">Once submitted, you cannot change your code.</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirmation(false)}
                className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
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
