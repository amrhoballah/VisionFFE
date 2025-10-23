import React, { useState } from 'react';
import HomePage from './components/HomePage';
import ExtractorApp from './ExtractorApp';
import RegistrationPage from './components/RegistrationPage';
import LoginPage from './components/LoginPage';
import { AuthProvider, useAuth } from './contexts/AuthContext';

const AppContent: React.FC = () => {
  const [view, setView] = useState<'home' | 'register' | 'login'>('home');
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-base-100 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  // If user is authenticated, show the main application.
  if (isAuthenticated) {
    return <ExtractorApp />;
  }

  // Otherwise, show the correct page based on the view state.
  switch (view) {
    case 'login':
      return <LoginPage 
        onLoginSuccess={() => {}} // Auth context will handle this automatically
        onNavigateToRegister={() => setView('register')}
        onBackToHome={() => setView('home')}
      />;
    case 'register':
      return <RegistrationPage 
        onBackToHome={() => setView('home')} 
        onNavigateToLogin={() => setView('login')}
      />;
    case 'home':
    default:
      return <HomePage 
        onGetStarted={() => setView('login')}
        onRegister={() => setView('register')}
        onLogin={() => setView('login')}
      />;
  }
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
