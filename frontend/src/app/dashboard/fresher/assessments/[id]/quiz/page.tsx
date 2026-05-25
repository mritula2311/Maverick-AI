"use client";

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api-service';
import { AssessmentDetail } from '@/lib/types';
import { useAuth } from '@/lib/auth-context';

export default function QuizSubmissionPage() {
  const params = useParams();
  const router = useRouter();
  const { token, isLoading: authLoading } = useAuth();
  const assessmentId = params.id as string;

  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const handleSubmitRef = useRef<() => void>(() => {});

  // Load assessment data
  useEffect(() => {
    const loadAssessment = async () => {
      // Wait for auth to be fully initialized
      if (authLoading) {
        console.log(`[QUIZ] Auth still loading...`);
        return;
      }

      // Redirect to login if no token
      if (!token) {
        console.log(`[QUIZ] No token found, redirecting to login`);
        router.push('/login');
        return;
      }

      try {
        setLoading(true);
        setError(null);

        console.log(`[QUIZ] Loading assessment ${assessmentId} with token length ${token.length}`);

        const result = await api.assessment.get(assessmentId, token);

        if (result.error) {
          console.log(`[QUIZ] Assessment API error:`, result.error);
          setError(result.error || "Failed to load assessment");
          setLoading(false);
          return;
        }

        if (result.data) {
          console.log(`[QUIZ] Assessment loaded successfully:`, result.data);
          setAssessment(result.data as any);
          setTimeRemaining(result.data.time_limit_minutes * 60); // Convert to seconds
        } else {
          console.log(`[QUIZ] No data in response`);
          setError("No assessment data received");
        }
        setLoading(false);
      } catch (err) {
        console.log(`[QUIZ] Exception:`, err);
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
          // Call outside the state setter to avoid side-effects inside a pure updater
          setTimeout(() => handleSubmitRef.current(), 0);
          return 0;
        }
        return next;
      });
    }, 1000);

    return () => clearTimeout(timer);
  }, [timeRemaining]);

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours > 0 ? `${hours}:` : ''}${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAnswerChange = (questionId: string, answer: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: answer,
    }));
  };

  const handleNext = () => {
    if (assessment && assessment.questions && currentQuestionIndex < assessment.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleQuestionJump = (index: number) => {
    setCurrentQuestionIndex(index);
  };

  const handleSubmit = async () => {
    if (!showConfirmation) {
      setShowConfirmation(true);
      return;
    }

    if (!token) {
      console.log(`[QUIZ] No token, redirecting to login`);
      router.push('/login');
      return;
    }

    setSubmitting(true);
    console.log(`[QUIZ] Submitting quiz with ${Object.keys(answers).length} answers`);

    // Submit via workflow API
    const result = await api.workflow.submit(
      {
        assessment_id: assessmentId,
        submission_type: 'quiz',
        answers,
      },
      token
    );

    console.log(`[QUIZ] Submission result:`, result);

    if (result.error) {
      console.log(`[QUIZ] Submission error:`, result.error);
      setError(result.error);
      setSubmitting(false);
      setShowConfirmation(false);
      return;
    }

    if (result.data) {
      console.log(`[QUIZ] Got trace_id=${result.data.trace_id}, redirecting to results`);
      // Redirect to results page with trace_id for status polling
      router.push(`/dashboard/fresher/assessments/${assessmentId}/results?trace_id=${result.data.trace_id}`);
    } else {
      console.log(`[QUIZ] No data in response`, result);
      setError('No response from server');
      setSubmitting(false);
      setShowConfirmation(false);
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

  const questions = assessment.questions ?? [];
  const currentQuestion = questions[currentQuestionIndex];
  const totalQuestions = questions.length;
  const answeredCount = Object.keys(answers).length;
  const progressPercentage = (answeredCount / totalQuestions) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="max-w-5xl mx-auto mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{assessment.title}</h1>
              <p className="text-gray-600 mt-1">{assessment.description}</p>
            </div>
            {timeRemaining !== null && (
              <div className={`text-2xl font-mono font-bold ${timeRemaining < 300 ? 'text-red-600 animate-pulse' : 'text-gray-800'}`}>
                ⏱️ {formatTime(timeRemaining)}
              </div>
            )}
          </div>

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Progress: {answeredCount} of {totalQuestions} answered</span>
              <span>{Math.round(progressPercentage)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Question Navigator Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-4 sticky top-4">
            <h3 className="font-semibold text-gray-800 mb-3">Question Navigator</h3>
            <div className="grid grid-cols-5 lg:grid-cols-4 gap-2">
              {questions.map((q, index) => {
                const isAnswered = answers[q.id] !== undefined;
                const isCurrent = index === currentQuestionIndex;
                return (
                  <button
                    key={q.id}
                    onClick={() => handleQuestionJump(index)}
                    className={`
                      w-10 h-10 rounded-lg font-semibold text-sm transition-all
                      ${isCurrent ? 'ring-2 ring-blue-500' : ''}
                      ${isAnswered
                        ? 'bg-green-500 text-white hover:bg-green-600'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }
                    `}
                  >
                    {index + 1}
                  </button>
                );
              })}
            </div>
            <div className="mt-4 text-xs text-gray-600 space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-500 rounded"></div>
                <span>Answered</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-gray-200 rounded"></div>
                <span>Not Answered</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Question Area */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg shadow-md p-8">
            {!currentQuestion ? (
              <div className="text-center py-12">
                <p className="text-gray-600">No questions available</p>
              </div>
            ) : (
              <>
            {/* Question Header */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold text-gray-800">
                Question {currentQuestionIndex + 1} of {totalQuestions}
              </h2>
              <span className="text-sm text-gray-600 bg-blue-100 px-3 py-1 rounded-full">
                {currentQuestion?.points || 0} points
              </span>
            </div>

            {/* Question Text */}
            <div className="mb-8">
              <p className="text-lg text-gray-900 leading-relaxed whitespace-pre-wrap">
                {currentQuestion?.question || 'No question text'}
              </p>
            </div>

            {/* Answer Input */}
            <div className="mb-8">
              {currentQuestion?.type === 'multiple_choice' && currentQuestion?.options && (
                <div className="space-y-3">
                  {currentQuestion?.options?.map((option, idx) => (
                    <label
                      key={idx}
                      className={`
                        flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all
                        ${answers[currentQuestion?.id] === option
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                        }
                      `}
                    >
                      <input
                        type="radio"
                        name={currentQuestion?.id || ''}
                        value={option}
                        checked={answers[currentQuestion?.id] === option}
                        onChange={(e) => handleAnswerChange(currentQuestion?.id || '', e.target.value)}
                        className="mt-1 mr-3 h-4 w-4 text-blue-600"
                      />
                      <span className="text-gray-800">{option}</span>
                    </label>
                  ))}
                </div>
              )}

              {currentQuestion?.type === 'true_false' && (
                <div className="space-y-3">
                  {['True', 'False'].map((option) => (
                    <label
                      key={option}
                      className={`
                        flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all
                        ${answers[currentQuestion?.id] === option
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                        }
                      `}
                    >
                      <input
                        type="radio"
                        name={currentQuestion?.id || ''}
                        value={option}
                        checked={answers[currentQuestion?.id] === option}
                        onChange={(e) => handleAnswerChange(currentQuestion?.id || '', e.target.value)}
                        className="mr-3 h-4 w-4 text-blue-600"
                      />
                      <span className="text-gray-800">{option}</span>
                    </label>
                  ))}
                </div>
              )}

              {currentQuestion?.type === 'short_answer' && (
                <textarea
                  value={answers[currentQuestion?.id] || ''}
                  onChange={(e) => handleAnswerChange(currentQuestion?.id || '', e.target.value)}
                  placeholder="Type your answer here..."
                  className="w-full p-4 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition min-h-[120px]"
                />
              )}
            </div>

            {/* Navigation Buttons */}
            <div className="flex justify-between items-center pt-6 border-t border-gray-200">
              <button
                onClick={handlePrevious}
                disabled={currentQuestionIndex === 0}
                className="flex items-center gap-2 px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← Previous
              </button>

              {currentQuestionIndex === totalQuestions - 1 ? (
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="px-8 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-semibold disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Quiz'}
                </button>
              ) : (
                <button
                  onClick={handleNext}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Next →
                </button>
              )}
            </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Submit Quiz?</h3>
            <p className="text-gray-600 mb-6">
              You have answered {answeredCount} out of {totalQuestions} questions.
              {answeredCount < totalQuestions && (
                <span className="block mt-2 text-orange-600 font-semibold">
                  Warning: {totalQuestions - answeredCount} question(s) remain unanswered.
                </span>
              )}
              <span className="block mt-2">Once submitted, you cannot change your answers.</span>
            </p>
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
