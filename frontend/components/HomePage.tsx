import React from 'react';
import { ImageIcon } from './Icons';

interface HomePageProps {
  onGetStarted: () => void;
  onRegister: () => void;
  onLogin: () => void;
}

const HomePage: React.FC<HomePageProps> = ({ onGetStarted, onRegister, onLogin }) => {
  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      {/* Header/Navigation */}
      <header className="absolute top-0 left-0 right-0 p-4 sm:p-6 lg:p-8 z-10">
        <nav className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-2">
            <ImageIcon className="w-8 h-8 text-blue-600"/>
            <h1 className="font-bold text-xl">Vision</h1>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={onGetStarted}
              className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors border border-blue-600 rounded-lg hover:bg-blue-50">
              Demo
            </button>
            <button
              onClick={onRegister}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
              Join Now
            </button>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="flex-grow flex items-center justify-center relative pt-20 pb-32">
        <div className="text-center px-4 max-w-6xl mx-auto">
          <h2 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-gray-900 mb-6">
            Where digital design connects<br />to real-world products
          </h2>
          <p className="text-xl sm:text-2xl text-gray-600 mb-12 max-w-3xl mx-auto">
            Vision is an AI agent for designers, automating FFE process cutting hours of sourcing into a few seconds.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button
              onClick={onGetStarted}
              className="px-8 py-4 text-lg font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl transform hover:scale-105 duration-300"
            >
              Design it. Detect it. Source it.
            </button>
            <p className="text-sm text-gray-500 italic">
              Vision connects your render to reality.
            </p>
          </div>
        </div>
      </main>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h3 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Create FFE schedules directly from your render
            </h3>
          </div>
          
          <div className="text-center mb-16">
            <h3 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
              How Vision.ai Works
            </h3>
            <p className="text-lg text-gray-600 mb-8">
              AI Technology that transforms how interior designers work with FFE scheduling
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
            {/* Feature 1 */}
            <div className="bg-white p-8 rounded-lg shadow-md hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <h4 className="text-xl font-semibold text-gray-900 mb-3">AI-Powered Detection</h4>
              <p className="text-gray-600">
                Advanced computer vision identifies furniture and fixtures in 3D renders and inspiration images with precision
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white p-8 rounded-lg shadow-md hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h4 className="text-xl font-semibold text-gray-900 mb-3">Real Supplier Matching</h4>
              <p className="text-gray-600">
                Instantly connect detected items with real supplier products, pricing, and availability data
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white p-8 rounded-lg shadow-md hover:shadow-xl transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h4 className="text-xl font-semibold text-gray-900 mb-3">Lightning Fast</h4>
              <p className="text-gray-600">
                Generate comprehensive FFE schedules in seconds, not hours. Reduce project timeline by 40%
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
            <div>
              <h5 className="font-bold text-xl mb-4">VISION.AI</h5>
            </div>
            <div>
              <p className="text-gray-400">vision.ffe@gmail.com</p>
            </div>
            <div className="flex flex-col gap-2">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">Accessibility Statement</a>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-gray-400 text-sm">
            <p>© 2025 by Vision.ai</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;