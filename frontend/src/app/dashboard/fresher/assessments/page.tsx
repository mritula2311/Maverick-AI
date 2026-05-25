"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronLeft } from 'lucide-react';
import { api } from '@/lib/api-service';
import { AssessmentDetail } from '@/lib/types';
import { useAuth } from '@/lib/auth-context';

export default function AssessmentsPage() {
  const router = useRouter();
  const { token, isLoading: authLoading } = useAuth();
  const [assessments, setAssessments] = useState<AssessmentDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'quiz' | 'assignment'>('all');

  useEffect(() => {
    const loadAssessments = async () => {
      if (authLoading) return;

      if (!token) {
        router.push('/login');
        return;
      }

      try {
        // Load all assessments (no fresher_id needed)
        const result = await api.assessment.list(token);

        if (result.error) {
          setError(result.error);
          setLoading(false);
          return;
        }

        if (result.data) {
          // Handle response structure: { items: [...] }
          const data = result.data as any;
          const assessmentList = Array.isArray(data) ? data : data.items || [];
          setAssessments(assessmentList);
        }
        setLoading(false);
      } catch (err) {
        setError('Failed to load assessments');
        setLoading(false);
      }
    };

    loadAssessments();
  }, [router, token, authLoading]);

  const filteredAssessments = assessments.filter((assessment) => {
    if (filter === 'all') return true;
    return assessment.assessment_type === filter;
  });

  const handleStartAssessment = (assessment: AssessmentDetail) => {
    if (assessment.assessment_type === 'quiz') {
      router.push(`/dashboard/fresher/assessments/${assessment.id}/quiz`);
    } else if (assessment.assessment_type === 'assignment') {
      router.push(`/dashboard/fresher/assessments/${assessment.id}/assignment`);
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'quiz':
        return 'bg-blue-100 text-blue-700';
      case 'assignment':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'quiz':
        return '📝';
      case 'assignment':
        return '📄';
      default:
        return '📋';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading assessments...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error Loading Assessments</h2>
          <p className="text-gray-600 mb-6">{error}</p>
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => router.push('/dashboard/fresher')}
          className="mb-6 flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Dashboard
        </button>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My Assessments</h1>
          <p className="text-gray-600">Complete assessments to track your learning progress</p>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setFilter('all')}
            className={`px-6 py-2 rounded-lg font-medium transition ${filter === 'all'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
          >
            All Assessments
          </button>
          <button
            onClick={() => setFilter('quiz')}
            className={`px-6 py-2 rounded-lg font-medium transition ${filter === 'quiz'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
          >
            📝 Quizzes
          </button>
          <button
            onClick={() => setFilter('assignment')}
            className={`px-6 py-2 rounded-lg font-medium transition ${filter === 'assignment'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
          >
            📄 Assignments
          </button>
        </div>

        {/* Assessments Grid */}
        {filteredAssessments.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-6xl mb-4">📚</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">No Assessments Found</h3>
            <p className="text-gray-600">
              {filter === 'all'
                ? 'There are no assessments available at the moment.'
                : `No ${filter} assessments available.`}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAssessments.map((assessment) => {
              const isAvailable = assessment.is_active;
              const hasStarted = assessment.available_from
                ? new Date(assessment.available_from) <= new Date()
                : true;
              const hasEnded = assessment.available_until
                ? new Date(assessment.available_until) < new Date()
                : false;

              const canStart = isAvailable && hasStarted && !hasEnded;

              return (
                <div
                  key={assessment.id}
                  className={`bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition ${!canStart ? 'opacity-75' : ''
                    }`}
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <span className="text-3xl">{getTypeIcon(assessment.assessment_type)}</span>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getTypeColor(assessment.assessment_type)}`}>
                        {assessment.assessment_type.toUpperCase()}
                      </span>
                    </div>

                    <h3 className="text-lg font-bold text-gray-900 mb-2">{assessment.title}</h3>
                    <p className="text-gray-600 text-sm mb-4 line-clamp-3">{assessment.description}</p>

                    <div className="space-y-2 mb-4 text-sm text-gray-600">
                      <div className="flex items-center gap-2">
                        <span>⏱️</span>
                        <span>{assessment.time_limit_minutes} minutes</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span>🎯</span>
                        <span>{assessment.max_score} points (Pass: {assessment.passing_score})</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span>🔄</span>
                        <span>Max {assessment.max_attempts} attempts</span>
                      </div>
                    </div>

                    {!canStart && (
                      <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <p className="text-sm text-yellow-800 font-medium">
                          {!isAvailable && '⚠️ Not available'}
                          {!hasStarted && '🔒 Not started yet'}
                          {hasEnded && '⏰ Assessment ended'}
                        </p>
                      </div>
                    )}

                    <button
                      onClick={() => handleStartAssessment(assessment)}
                      disabled={!canStart}
                      className={`w-full py-2 rounded-lg font-semibold transition ${canStart
                          ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        }`}
                    >
                      {canStart ? 'Start Assessment' : 'Not Available'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
