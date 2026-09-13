import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import Signup from './pages/Signup';
import QuestionList from './pages/QuestionList';
import MyAttempts from './pages/MyAttempts';
import CaseWorkspace from './pages/CaseWorkspace';
import ScoreDashboard from './pages/ScoreDashboard';
import { getAuthToken, setAuthToken } from './api/client';

function Navigation({ onLogout }) {
  const navigate = useNavigate();

  const handleLogoutClick = () => {
    onLogout();
    navigate('/login');
  };

  return (
    <header className="bg-slate-800 text-white shadow-md">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/questions" className="flex items-center gap-2 font-black text-lg tracking-tight text-white hover:opacity-90">
          <span>⚡</span> PromptBench
        </Link>
        <nav className="flex items-center gap-6">
          <Link to="/questions" className="text-sm font-semibold hover:text-slate-200 transition duration-150">
            Dashboard
          </Link>
          <Link to="/attempts" className="text-sm font-semibold hover:text-slate-200 transition duration-150">
            My Attempts
          </Link>
          <button
            onClick={handleLogoutClick}
            className="px-3.5 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-xs font-bold transition duration-150"
          >
            Log Out
          </button>
        </nav>
      </div>
    </header>
  );
}

function ProtectedRoute({ children, isAuthenticated }) {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  const [token, setToken] = useState(getAuthToken());

  // Watch for changes in client auth token store
  const isAuthenticated = !!token;

  const handleLogout = () => {
    setAuthToken('');
    setToken('');
  };

  const handleAuthChange = () => {
    setToken(getAuthToken());
  };

  // Re-sync auth status on changes
  useEffect(() => {
    const checkToken = setInterval(() => {
      const activeToken = getAuthToken();
      if (activeToken !== token) {
        setToken(activeToken);
      }
    }, 500);
    return () => clearInterval(checkToken);
  }, [token]);

  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-slate-50 font-sans">
        {isAuthenticated && <Navigation onLogout={handleLogout} />}
        
        <main className="flex-grow">
          <Routes>
            {/* Public Routes */}
            <Route
              path="/login"
              element={isAuthenticated ? <Navigate to="/questions" replace /> : <Login />}
            />
            <Route
              path="/signup"
              element={isAuthenticated ? <Navigate to="/questions" replace /> : <Signup />}
            />

            {/* Protected Routes */}
            <Route
              path="/questions"
              element={
                <ProtectedRoute isAuthenticated={isAuthenticated}>
                  <QuestionList />
                </ProtectedRoute>
              }
            />
            <Route
              path="/attempts"
              element={
                <ProtectedRoute isAuthenticated={isAuthenticated}>
                  <MyAttempts />
                </ProtectedRoute>
              }
            />
            <Route
              path="/case/:submissionId"
              element={
                <ProtectedRoute isAuthenticated={isAuthenticated}>
                  <CaseWorkspace />
                </ProtectedRoute>
              }
            />
            <Route
              path="/results/:submissionId"
              element={
                <ProtectedRoute isAuthenticated={isAuthenticated}>
                  <ScoreDashboard />
                </ProtectedRoute>
              }
            />

            {/* Catch-all Redirect */}
            <Route
              path="*"
              element={<Navigate to={isAuthenticated ? "/questions" : "/login"} replace />}
            />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
