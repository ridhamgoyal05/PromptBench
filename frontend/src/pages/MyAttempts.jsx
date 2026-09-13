import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import client from '../api/client';

export default function MyAttempts() {
  const [attempts, setAttempts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAttempts = async () => {
      try {
        const response = await client.get('/evaluations/history');
        setAttempts(response.data);
      } catch (err) {
        setError('Something went wrong. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchAttempts();
  }, []);

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-slate-600 font-medium">Loading your history...</span>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">My Attempts</h1>
          <p className="text-slate-500 mt-2">Browse your completed case study evaluations and scores.</p>
        </div>
        <Link
          to="/questions"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition duration-200"
        >
          New Attempt
        </Link>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 text-sm mb-6">
          {error}
        </div>
      )}

      {attempts.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <span className="text-4xl">📝</span>
          <h3 className="text-lg font-bold text-slate-800 mt-3">No attempts yet</h3>
          <p className="text-slate-500 text-sm mt-1 max-w-md mx-auto">
            You haven't completed any case study sessions. Go back to the dashboard and try one out!
          </p>
          <Link
            to="/questions"
            className="mt-5 inline-block px-4 py-2 bg-slate-800 text-white rounded-lg text-sm font-semibold hover:bg-slate-900 transition duration-200"
          >
            Browse Case Studies
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 text-xs font-bold uppercase tracking-wider">
                <th className="px-6 py-4">Case Study</th>
                <th className="px-6 py-4">Score</th>
                <th className="px-6 py-4">Completed On</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {attempts.map((attempt) => (
                <tr key={attempt.submission_id} className="hover:bg-slate-50 transition duration-150">
                  <td className="px-6 py-4 font-semibold text-slate-800">{attempt.question_title}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-100">
                      {attempt.overall_score} / 100
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-500">{formatDate(attempt.submitted_at)}</td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      to={`/results/${attempt.submission_id}`}
                      className="inline-block px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded text-xs transition duration-200"
                    >
                      View Results
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
