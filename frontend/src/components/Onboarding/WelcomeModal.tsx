import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface WelcomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  isFirstLogin?: boolean;
}

const WelcomeModal: React.FC<WelcomeModalProps> = ({ isOpen, onClose, isFirstLogin = false }) => {
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      title: `Welcome to Duelo de Plumas, ${user?.username}!`,
      content: (
        <div className="space-y-4">
          <p className="text-gray-600">
            You've successfully joined our literary contest platform where writers and AI collaborate in creative competitions.
          </p>
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
      title: "What You Can Do Here",
      content: (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">📝 Create & Submit Texts</h4>
              <p className="text-blue-700 text-sm">Write stories, poems, or essays and submit them to contests.</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-medium text-green-900 mb-2">🏆 Join Contests</h4>
              <p className="text-green-700 text-sm">Participate in literary competitions as an author or judge.</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <h4 className="font-medium text-purple-900 mb-2">🤖 AI Collaboration</h4>
              <p className="text-purple-700 text-sm">Create AI agents to help with writing and judging.</p>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <h4 className="font-medium text-orange-900 mb-2">⚖️ Judge & Evaluate</h4>
              <p className="text-orange-700 text-sm">Evaluate submissions and help determine contest winners.</p>
            </div>
          </div>
        </div>
      )
    },
    {
      title: "Quick Start Guide",
      content: (
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900 mb-3">Recommended first steps:</h4>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-sm font-medium">1</span>
              <div>
                <p className="font-medium">Explore Public Contests</p>
                <p className="text-sm text-gray-600">Browse available contests to see what interests you.</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-sm font-medium">2</span>
              <div>
                <p className="font-medium">Write Your First Text</p>
                <p className="text-sm text-gray-600">Create a story, poem, or essay using our editor or AI writer.</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-sm font-medium">3</span>
              <div>
                <p className="font-medium">Create an AI Agent</p>
                <p className="text-sm text-gray-600">Set up an AI writer or judge to assist in your literary journey.</p>
              </div>
            </div>
          </div>
        </div>
      )
    }
  ];

  if (!isOpen) return null;

  const isLastStep = currentStep === steps.length - 1;
  const isFirstStep = currentStep === 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{steps[currentStep].title}</h2>
              {isFirstLogin && (
                <p className="text-sm text-gray-500 mt-1">Step {currentStep + 1} of {steps.length}</p>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              title="Close onboarding"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="mb-8">
            {steps[currentStep].content}
          </div>

          {/* Progress bar for first login */}
          {isFirstLogin && (
            <div className="mb-6">
              <div className="bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Actions */}
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
                    onClick={onClose}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
                  >
                    Browse Contests
                  </Link>
                  <Link
                    to="/dashboard?tab=texts"
                    onClick={onClose}
                    className="px-6 py-2 border border-indigo-600 text-indigo-600 rounded-md hover:bg-indigo-50 transition-colors"
                  >
                    Create Text
                  </Link>
                </div>
              ) : (
                <>
                  {!isFirstLogin && (
                    <button
                      onClick={onClose}
                      className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                    >
                      Skip Tour
                    </button>
                  )}
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

export default WelcomeModal; 