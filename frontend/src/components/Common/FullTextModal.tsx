import React from 'react';

interface FullTextModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  content: string;
  author?: string;
}

const FullTextModal: React.FC<FullTextModalProps> = ({
  isOpen,
  onClose,
  title,
  content,
  author
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full h-[80vh] flex flex-col mx-4">
        {/* Modal header */}
        <div className="px-6 py-4 border-b flex justify-between items-center flex-shrink-0">
          <div>
            <h3 className="text-xl font-bold text-gray-900">
              {title || 'Text Content'}
            </h3>
            {author && (
              <p className="text-sm text-gray-600 mt-1">by {author}</p>
            )}
          </div>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
            aria-label="Close modal"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Modal content */}
        <div className="px-6 py-4 overflow-y-auto flex-grow">
          <div className="prose prose-sm max-w-none">
            <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded text-base leading-relaxed">
              {content}
            </pre>
          </div>
        </div>
        
        {/* Modal footer */}
        <div className="px-6 py-4 border-t bg-gray-50 flex-shrink-0">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FullTextModal; 