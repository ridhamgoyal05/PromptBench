import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client';

export default function ScoreDashboard() {
  const { submissionId } = useParams();
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchEvaluation = async () => {
      try {
        const response = await client.get(`/evaluations/${submissionId}`);
        setEvaluation(response.data);
      } catch (err) {
        setError('Something went wrong. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchEvaluation();
  }, [submissionId]);

  const getDimensionLabel = (dimKey) => {
    switch (dimKey) {
      case 'clarifying_questions': return 'Clarifying Questions';
      case 'iteration_quality': return 'Iteration Quality';
      case 'hallucination_catching': return 'Hallucination Catching';
      case 'final_answer_quality': return 'Final Answer Quality';
      default: return dimKey.replace(/_/g, ' ');
    }
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'text-emerald-600 bg-emerald-50';
    if (score >= 5) return 'text-amber-600 bg-amber-50';
    return 'text-rose-600 bg-rose-50';
  };

  const getProgressBarColor = (score) => {
    if (score >= 8) return 'bg-emerald-500';
    if (score >= 5) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20 min-h-[500px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-slate-600 font-medium font-sans">Calculating evaluation...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-12 p-6 bg-white rounded-xl border border-slate-200 shadow text-center font-sans">
        <span className="text-4xl">⚠️</span>
        <h2 className="text-xl font-bold mt-3 text-slate-800">Cannot Load Evaluation</h2>
        <p className="text-slate-500 mt-2">{error}</p>
        <Link to="/questions" className="mt-6 inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-sm">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const scores = evaluation?.dimension_scores_json || {};
  const flags = evaluation?.anti_gaming_flags || [];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 font-sans">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">Evaluation Results</h1>
        <p className="text-slate-500 mt-1">Case study: <strong className="text-slate-700">{evaluation?.question_title}</strong></p>
      </div>

      {/* Warning banner for anti-gaming flags */}
      {flags.length > 0 && (
        <div className="mb-6 bg-amber-50 rounded-xl p-4 border border-amber-200 text-amber-800 flex flex-col gap-1.5 shadow-sm text-sm">
          <span className="font-bold flex items-center gap-1.5">
            ⚠️ Activity Flags Detected
          </span>
          <ul className="list-disc list-inside space-y-1">
            {flags.map((flag, idx) => (
              <li key={idx} className="leading-relaxed">{flag}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Overall Score Circle */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col items-center justify-center shadow-sm">
          <h2 className="text-sm font-bold text-slate-600 uppercase tracking-wider mb-4">Overall Score</h2>
          <div className="relative flex items-center justify-center">
            {/* Simple circle display */}
            <div className="w-32 h-32 rounded-full border-8 border-slate-100 flex flex-col items-center justify-center">
              <span className="text-3xl font-black text-slate-800">{evaluation?.overall_score}</span>
              <span className="text-xs text-slate-400 font-bold uppercase">out of 100</span>
            </div>
          </div>
        </div>

        {/* Dimension Breakdown */}
        <div className="md:col-span-2 bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
          <h2 className="text-sm font-bold text-slate-600 uppercase tracking-wider mb-4">Rubric Scores</h2>
          <div className="space-y-4">
            {Object.keys(scores).map((key) => {
              const scoreVal = scores[key];
              return (
                <div key={key} className="space-y-1">
                  <div className="flex justify-between items-center text-sm font-medium text-slate-700">
                    <span>{getDimensionLabel(key)}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${getScoreColor(scoreVal)}`}>
                      {scoreVal} / 10
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${getProgressBarColor(scoreVal)}`}
                      style={{ width: `${scoreVal * 10}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Judge Feedback Reasoning */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-8">
        <h2 className="text-sm font-bold text-slate-600 uppercase tracking-wider mb-3">Evaluator Feedback</h2>
        <div className="text-slate-700 text-sm leading-relaxed whitespace-pre-wrap bg-slate-50 border border-slate-100 rounded-xl p-4">
          {evaluation?.judge_reasoning}
        </div>
      </div>

      {/* Candidate Response Transcript */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm mb-8">
        <h2 className="text-sm font-bold text-slate-600 uppercase tracking-wider mb-3">Saved Conversation</h2>
        <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
          {evaluation?.transcript?.map((turn, idx) => (
            <div key={idx} className={`p-3 rounded-lg text-xs leading-relaxed ${
              turn.role === 'user' ? 'bg-blue-50 border border-blue-100 text-blue-800' : 'bg-slate-50 border border-slate-100 text-slate-700'
            }`}>
              <strong className="block uppercase tracking-wider text-[10px] mb-1">
                {turn.role === 'user' ? 'Candidate' : 'Helper AI'}
              </strong>
              {turn.content}
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-4 justify-end">
        <Link
          to="/attempts"
          className="px-6 py-2.5 bg-slate-100 text-slate-700 font-semibold rounded-xl text-sm border border-slate-300 hover:bg-slate-200 text-center transition duration-200"
        >
          View My Attempts
        </Link>
        <Link
          to="/questions"
          className="px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-xl text-sm hover:bg-blue-700 text-center transition duration-200 shadow"
        >
          Try Another Case
        </Link>
      </div>
    </div>
  );
}
