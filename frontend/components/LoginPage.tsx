import React, { useState } from 'react';
import { ImageIcon } from './Icons';
import { useAuth } from '../contexts/AuthContext';

interface LoginPageProps {
  onLoginSuccess: () => void;
  onNavigateToRegister: () => void;
  onBackToHome: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess, onNavigateToRegister, onBackToHome }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const { login, isLoading } = useAuth();

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError(null);

        try {
            await login({ username, password });
            onLoginSuccess();
        } catch (err: any) {
            setError(err.message || 'Failed to log in. Please check your credentials and try again.');
        }
    };

    return (
        <div className="min-h-screen bg-base-100 text-base-content flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-md">
                <header className="text-center mb-8">
                    <div className="flex items-center justify-center gap-3 mb-2">
                        <ImageIcon className="w-8 h-8 text-brand-primary" />
                        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
                            Welcome Back
                        </h1>
                    </div>
                    <p className="text-base-content/70">
                        Log in to continue your creative journey.
                    </p>
                </header>

                <main className="bg-base-200 p-8 rounded-xl shadow-lg">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-base-content/80 mb-2">Username or Email</label>
                            <input 
                                type="text" 
                                id="username" 
                                name="username" 
                                required 
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full bg-base-300 border border-base-300 text-base-content rounded-lg p-2.5 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition" 
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-base-content/80 mb-2">Password</label>
                            <input 
                                type="password" 
                                id="password"
                                name="password" 
                                required 
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-base-300 border border-base-300 text-base-content rounded-lg p-2.5 focus:ring-2 focus:ring-brand-primary focus:border-brand-primary transition" 
                            />
                        </div>

                        {error && (
                            <div className="text-center bg-red-900/50 border border-red-700 text-red-200 text-sm p-3 rounded-lg">
                                <p>{error}</p>
                            </div>
                        )}

                        <div className="flex flex-col-reverse sm:flex-row items-center justify-between gap-4 pt-2">
                             <button
                                type="button"
                                onClick={onBackToHome}
                                className="w-full sm:w-auto px-6 py-3 text-sm font-semibold text-base-content bg-base-300 rounded-lg hover:bg-opacity-80 transition-all"
                            >
                                Back to Home
                            </button>
                            <button 
                                type="submit" 
                                disabled={isLoading}
                                className="w-full sm:w-auto flex items-center justify-center px-8 py-3 font-bold text-white bg-gradient-to-r from-brand-primary to-brand-secondary rounded-lg hover:scale-105 transform transition-transform duration-300 ease-in-out shadow-lg disabled:opacity-60 disabled:cursor-not-allowed disabled:scale-100"
                            >
                                {isLoading ? (
                                    <div className="w-5 h-5 border-2 border-white/50 border-t-white rounded-full animate-spin"></div>
                                ) : (
                                    'Log In'
                                )}
                            </button>
                        </div>

                        <div className="text-center text-sm text-base-content/70 pt-2">
                            <p>
                                Don't have an account?{' '}
                                <button type="button" onClick={onNavigateToRegister} className="font-medium text-brand-primary hover:underline">
                                    Register
                                </button>
                            </p>
                        </div>
                    </form>
                </main>
            </div>
        </div>
    );
};

export default LoginPage;
