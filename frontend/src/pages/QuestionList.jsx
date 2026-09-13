import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';

export default function QuestionList() {
  const [questions, setQuestions] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const response = await client.get('/questions');
        setQuestions(response.data);
      } catch (err) {
        setError('Something went wrong. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchQuestions();
  }, []);

  const handleStartCase = async (questionId) => {
    try {
      const response = await client.post('/submissions', { question_id: questionId });
      const submissionId = response.data.submission_id;
      navigate(`/case/${submissionId}`);
    } catch (err) {
      setError('Something went wrong. Please try again.');
    }
  };

  const getDifficultyBadgeColor = (diff) => {
    switch (diff.toLowerCase()) {
      case 'easy':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'medium':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'hard':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const getCategoryLabel = (cat) => {
    switch (cat) {
      case 'data_diagnosis':
        return 'Data Diagnosis';
      case 'strategy_generation':
        return 'Strategy Generation';
      case 'customer_reasoning':
        return 'Customer Reasoning';
      default:
        return cat;
    }
  };

  const getCategoryBadgeColor = (cat) => {
    switch (cat) {
      case 'data_diagnosis':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'strategy_generation':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'customer_reasoning':
        return 'bg-violet-50 text-violet-700 border-violet-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-slate-600 font-medium">Loading cases...</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">AI Case Studies</h1>
        <p className="text-slate-500 mt-2">
          Select a case study to practice collaborating with an AI partner. We will evaluate how well you leverage the assistant to formulate your final recommendation.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 text-sm mb-6">
          {error}
        </div>
      )}

      {questions.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <p className="text-slate-500 font-medium text-lg">No cases found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {questions.map((q) => (
            <div
              key={q.id}
              className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col justify-between shadow-sm hover:shadow transition duration-200"
            >
              <div>
                <div className="flex flex-wrap gap-2 mb-3">
                  <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${getDifficultyBadgeColor(q.difficulty)}`}>
                    {q.difficulty.toUpperCase()}
                  </span>
                  <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${getCategoryBadgeColor(q.category)}`}>
                    {getCategoryLabel(q.category)}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-800 mb-2">{q.title}</h3>
                <p className="text-slate-500 text-sm line-clamp-3 mb-6">
                  {q.title === 'Sudden Churn Spike' && 'Analyze monthly SaaS user logs and cancel reasons to solve a drop in metrics.'}
                  {q.title === 'New Market Entry' && 'Select the ideal international launch territory comparing Germany and Brazil.'}
                  {q.title === 'Angry Customer Escalation' && 'Resolve a high-value customer double-billing incident gracefully.'}
                  {q.title === 'Sales Decline Diagnosis' && 'Identify why an e-commerce platform sales collapsed by 15% in Q3.'}
                  {q.title === 'Product Launch Strategy' && 'Draft the launch timeline, pricing model, and customer segments.'}
                </p>
              </div>

              <button
                onClick={() => handleStartCase(q.id)}
                className="w-full py-2 bg-slate-800 hover:bg-slate-900 text-white font-semibold rounded-lg text-sm transition duration-200 shadow-sm"
              >
                Start Practice Case
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
