import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const OnboardingPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      title: "Welcome to Duelo de Plumas!",
      content: (
        <div className="space-y-6">
          <div className="text-center">
            <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C20.832 18.477 19.246 18 17.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Welcome, {user?.username}!
            </h3>
            <p className="text-gray-600">
              You've joined the premier literary contest platform where writers and AI collaborate in creative competitions.
            </p>
          </div>
          
          <div className="bg-indigo-50 p-4 rounded-lg">
            <h4 className="font-medium text-indigo-900 mb-2">Your Starting Credits</h4>
            <p className="text-indigo-700 text-sm">
              You have <span className="font-bold">{user?.credits || 0} credits</span> to use for AI-powered writing and judging.
            </p>
          </div>
        </div>
      )
    },
    {
      title: "Platform Features",
      content: (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">What You Can Do Here</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mb-2">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </div>
              <h4 className="font-medium text-blue-900 mb-2">📝 Create & Submit Texts</h4>
              <p className="text-blue-700 text-sm">Write stories, poems, or essays and submit them to contests.</p>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mb-2">
                <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h4 className="font-medium text-green-900 mb-2">🏆 Join Contests</h4>
              <p className="text-green-700 text-sm">Participate in literary competitions as an author or judge.</p>
            </div>
            
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mb-2">
                <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h4 className="font-medium text-purple-900 mb-2">🤖 AI Collaboration</h4>
              <p className="text-purple-700 text-sm">Create AI agents to help with writing and judging.</p>
            </div>
            
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center mb-2">
                <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16l-3-3m3 3l3-3" />
                </svg>
              </div>
              <h4 className="font-medium text-orange-900 mb-2">⚖️ Judge & Evaluate</h4>
              <p className="text-orange-700 text-sm">Evaluate submissions and help determine contest winners.</p>
            </div>
          </div>
        </div>
      )
    },
    {
      title: "Getting Started",
      content: (
        <div className="space-y-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recommended First Steps</h3>
          <div className="space-y-4">
            <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
              <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-sm font-medium">1</span>
              <div>
                <p className="font-medium text-gray-900">Explore Public Contests</p>
                <p className="text-sm text-gray-600 mb-2">Browse available contests to see what interests you.</p>
                <Link 
                  to="/contests" 
                  className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                >
                  Browse Contests →
                </Link>
              </div>
            </div>
            
            <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
              <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-sm font-medium">2</span>
              <div>
                <p className="font-medium text-gray-900">Write Your First Text</p>
                <p className="text-sm text-gray-600 mb-2">Create a story, poem, or essay using our editor or AI writer.</p>
                <Link 
                  to="/dashboard?tab=texts" 
                  className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                >
                  Create Text →
                </Link>
              </div>
            </div>
            
            <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
              <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-sm font-medium">3</span>
              <div>
                <p className="font-medium text-gray-900">Set Up Your Dashboard</p>
                <p className="text-sm text-gray-600 mb-2">Customize your workspace and create AI agents to assist you.</p>
                <Link 
                  to="/dashboard" 
                  className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                >
                  Go to Dashboard →
                </Link>
              </div>
            </div>
          </div>
        </div>
      )
    }
  ];

  const isLastStep = currentStep === steps.length - 1;
  const isFirstStep = currentStep === 0;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow-sm rounded-lg">
        <div className="px-6 py-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{steps[currentStep].title}</h1>
            <p className="text-sm text-gray-500">Step {currentStep + 1} of {steps.length}</p>
          </div>

          {/* Progress bar */}
          <div className="mb-8">
            <div className="bg-gray-200 rounded-full h-2">
              <div 
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
              />
            </div>
          </div>

          {/* Content */}
          <div className="mb-8">
            {steps[currentStep].content}
          </div>

          {/* Navigation */}
          <div className="flex justify-between items-center">
            <div>
              {!isFirstStep && (
                <button
                  onClick={() => setCurrentStep(currentStep - 1)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  ← Previous
                </button>
              )}
            </div>
            
            <div className="flex space-x-3">
              {isLastStep ? (
                <div className="flex space-x-3">
                  <Link
                    to="/contests"
                    className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
                  >
                    Explore Contests
                  </Link>
                  <Link
                    to="/dashboard"
                    className="px-6 py-2 border border-indigo-600 text-indigo-600 rounded-md hover:bg-indigo-50 transition-colors"
                  >
                    Go to Dashboard
                  </Link>
                </div>
              ) : (
                <>
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    Skip Tour
                  </button>
                  <button
                    onClick={() => setCurrentStep(currentStep + 1)}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
                  >
                    Next →
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingPage; 