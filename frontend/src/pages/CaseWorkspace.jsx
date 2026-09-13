import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import client from '../api/client';

export default function CaseWorkspace() {
  const { submissionId } = useParams();
  const navigate = useNavigate();

  const [question, setQuestion] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [finalAnswer, setFinalAnswer] = useState('');
  const [status, setStatus] = useState('in_progress');

  const [message, setMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);

  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState('');

  const chatEndRef = useRef(null);

  useEffect(() => {
    const fetchSubmission = async () => {
      try {
        const response = await client.get(`/submissions/${submissionId}`);
        const data = response.data;
        
        // If already successfully submitted, go straight to results
        if (data.status === 'submitted') {
          navigate(`/results/${submissionId}`);
          return;
        }

        setQuestion(data.question);
        setTranscript(data.transcript || []);
        setFinalAnswer(data.final_answer_text || '');
        setStatus(data.status);
      } catch (err) {
        if (err.response && err.response.status === 403) {
          setError("Forbidden: You do not have permission to access this case session.");
        } else {
          setError("Something went wrong. Please try again.");
        }
      } finally {
        setPageLoading(false);
      }
    };
    fetchSubmission();
  }, [submissionId, navigate]);

  useEffect(() => {
    // Scroll to bottom of chat
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim() || chatLoading) return;

    const userMsg = message;
    setMessage('');
    setChatLoading(true);
    setError('');

    // Optimistically add user turn to local state
    setTranscript((prev) => [...prev, { role: 'user', content: userMsg }]);

    try {
      const response = await client.post(`/submissions/${submissionId}/message`, { message: userMsg });
      setTranscript((prev) => [...prev, { role: 'assistant', content: response.data.reply }]);
    } catch (err) {
      // Remove the optimistically added user turn on failure to match backend state
      setTranscript((prev) => prev.slice(0, -1));
      setError('Something went wrong. Please try again.');
    } finally {
      setChatLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!finalAnswer.trim() || submitLoading) return;
    
    setSubmitLoading(true);
    setError('');

    try {
      await client.post(`/submissions/${submissionId}/submit`, { final_answer_text: finalAnswer });
      navigate(`/results/${submissionId}`);
    } catch (err) {
      setStatus('evaluation_failed');
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Something went wrong. Please try again.');
      }
    } finally {
      setSubmitLoading(false);
    }
  };

  const getDifficultyBadgeColor = (diff) => {
    switch (diff?.toLowerCase()) {
      case 'easy': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'medium': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'hard': return 'bg-rose-50 text-rose-700 border-rose-200';
      default: return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  if (pageLoading) {
    return (
      <div className="flex justify-center items-center py-20 min-h-[500px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-slate-600 font-medium font-sans">Loading workspace...</span>
      </div>
    );
  }

  if (error && !question) {
    return (
      <div className="max-w-2xl mx-auto mt-12 p-6 bg-white rounded-xl border border-slate-200 shadow text-center">
        <span className="text-4xl">⚠️</span>
        <h2 className="text-xl font-bold mt-3 text-slate-800">Cannot Load Case Workspace</h2>
        <p className="text-slate-500 mt-2">{error}</p>
        <Link to="/questions" className="mt-6 inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-sm">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-64px)] flex flex-col md:flex-row overflow-hidden font-sans">
      {/* LEFT PANE: Prompt, Context, final answer input */}
      <div className="w-full md:w-1/2 flex flex-col border-r border-slate-200 bg-white overflow-y-auto p-6 space-y-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${getDifficultyBadgeColor(question?.difficulty)}`}>
              {question?.difficulty?.toUpperCase()}
            </span>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full border bg-slate-50 text-slate-700 border-slate-200">
              {question?.category?.replace('_', ' ')}
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-800 tracking-tight">{question?.title}</h1>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 text-sm">
            {error}
          </div>
        )}

        {status === 'evaluation_failed' && (
          <div className="bg-amber-50 text-amber-800 p-4 rounded-xl border border-amber-200 text-sm">
            <strong>Evaluation failed:</strong> We couldn't complete the evaluation of your response. You can refine your final answer below and try submitting again.
          </div>
        )}

        <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
          <h2 className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Case Study Prompt</h2>
          <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-wrap">{question?.prompt_text}</p>
        </div>

        <div>
          <h2 className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Public Dataset / Context</h2>
          <pre className="bg-slate-900 text-slate-200 rounded-xl p-4 text-xs overflow-x-auto leading-relaxed whitespace-pre-wrap font-mono">
            {question?.context_data}
          </pre>
        </div>

        <div className="flex-grow flex flex-col min-h-[200px]">
          <h2 className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Your Final Written Answer</h2>
          <textarea
            value={finalAnswer}
            onChange={(e) => setFinalAnswer(e.target.value)}
            disabled={submitLoading}
            className="w-full flex-grow px-4 py-3 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none"
            placeholder="Type your final diagnosis and recommendation here based on your investigation..."
          />
        </div>

        <div>
          <button
            onClick={handleSubmitAnswer}
            disabled={submitLoading || !finalAnswer.trim()}
            className={`w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm shadow transition duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 flex justify-center items-center ${
              (submitLoading || !finalAnswer.trim()) ? 'opacity-70 cursor-not-allowed' : ''
            }`}
          >
            {submitLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                Evaluating your response...
              </>
            ) : status === 'evaluation_failed' ? (
              'Retry Evaluation'
            ) : (
              'Submit Final Answer'
            )}
          </button>
        </div>
      </div>

      {/* RIGHT PANE: Chat panel with Helper AI */}
      <div className="w-full md:w-1/2 flex flex-col bg-slate-50 overflow-hidden h-full">
        {/* Helper AI Headers */}
        <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🤖</span>
            <div>
              <h2 className="text-sm font-bold text-slate-800">Helper AI Partner</h2>
              <p className="text-xs text-slate-500">Collaborate to query facts or validate logic</p>
            </div>
          </div>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">
            Active
          </span>
        </div>

        {/* Chat History Container */}
        <div className="flex-grow overflow-y-auto p-6 space-y-4">
          {transcript.length === 0 ? (
            <div className="h-full flex flex-col justify-center items-center text-center p-8">
              <span className="text-3xl text-slate-400">💬</span>
              <p className="text-sm font-medium text-slate-600 mt-2">Start chatting with the Helper AI</p>
              <p className="text-xs text-slate-500 mt-1 max-w-xs">
                Ask clarifying questions or verify observations about the case. The Helper AI does not know the rubric or secret notes.
              </p>
            </div>
          ) : (
            transcript.map((turn, idx) => (
              <div key={idx} className={`flex ${turn.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                    turn.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-white text-slate-700 rounded-bl-none border border-slate-200'
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{turn.content}</p>
                </div>
              </div>
            ))
          )}

          {chatLoading && (
            <div className="flex justify-start">
              <div className="bg-white text-slate-500 rounded-2xl rounded-bl-none border border-slate-200 px-4 py-3 text-sm shadow-sm flex items-center">
                <div className="flex space-x-1 mr-2">
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                AI is thinking...
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Chat input box */}
        <form onSubmit={handleSendMessage} className="bg-white border-t border-slate-200 p-4 flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={chatLoading}
            placeholder="Ask your helper assistant a question..."
            className="flex-grow px-4 py-2 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
          <button
            type="submit"
            disabled={chatLoading || !message.trim()}
            className={`px-5 py-2 bg-slate-800 hover:bg-slate-900 text-white font-semibold rounded-xl text-sm transition duration-200 shadow-sm ${
              (chatLoading || !message.trim()) ? 'opacity-70 cursor-not-allowed' : ''
            }`}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
