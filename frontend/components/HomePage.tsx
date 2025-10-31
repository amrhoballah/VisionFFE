import React from 'react';
import { ImageIcon } from './Icons';

interface HomePageProps {
  onGetStarted: () => void;
  onRegister: () => void;
  onLogin: () => void;
}

const HomePage: React.FC<HomePageProps> = ({ onGetStarted, onRegister, onLogin }) => {
  return (
    <div className="min-h-screen bg-base-100 text-base-content flex flex-col">
      <header className="absolute top-0 left-0 right-0 p-4 sm:p-6 lg:p-8 z-10">
        <nav className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-2 text-base-content">
            <ImageIcon className="w-6 h-6 text-brand-primary"/>
            <h1 className="font-semibold text-lg hidden sm:block">VisionFFE</h1>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={onLogin}
              className="px-4 py-2 text-sm font-medium text-base-content bg-base-200 rounded-lg hover:bg-base-300 transition-colors">
              Login
            </button>
            <button
              onClick={onRegister}
              className="px-4 py-2 text-sm font-bold text-white bg-gradient-to-r from-brand-primary to-brand-secondary rounded-lg hover:scale-105 transform transition-transform duration-300 ease-in-out">
              Register
            </button>
          </div>
        </nav>
      </header>

      <main className="flex-grow flex items-center justify-center">
        <div className="text-center px-4 relative z-0">
            <div className="absolute -inset-20 bg-gradient-to-r from-brand-primary to-brand-secondary opacity-10 blur-3xl rounded-full" aria-hidden="true"></div>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-brand-primary to-brand-secondary">
                Unlock Your Room's Potential.
            </h2>
            <p className="mt-4 max-w-2xl mx-auto text-lg text-base-content/70">
                Effortlessly extract furniture and decor from any image. Upload multiple angles of a room and let our AI isolate each item for you.
            </p>
            <div className="mt-8">
                <button
                onClick={onGetStarted}
                className="px-8 py-3 text-lg font-bold text-white bg-gradient-to-r from-brand-primary to-brand-secondary rounded-full hover:scale-105 transform transition-transform duration-300 ease-in-out shadow-lg"
                >
                Get Started Now
                </button>
            </div>
        </div>
      </main>
      
      <footer className="text-center p-4 text-base-content/50 text-sm">
        <p>Powered by Gemini</p>
      </footer>
    </div>
  );
};

export default HomePage;