import React from 'react';

interface AIJudgeConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  estimatedCost: number;
  isSubmitting: boolean;
}

const AIJudgeConfirmationModal: React.FC<AIJudgeConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  estimatedCost,
  isSubmitting
}) => {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 className="text-lg font-bold mb-4">Confirm AI Judge Execution</h3>
        <p className="mb-4">
          You are about to use <span className="font-bold">{estimatedCost} credits</span> to evaluate all submissions in this contest using an AI judge.
        </p>
        <p className="text-amber-600 text-sm mb-4">
          <strong>Warning:</strong> This action cannot be undone. The AI judge will evaluate all submissions and the results will be immediately visible to participants.
        </p>
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="px-4 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isSubmitting}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {isSubmitting ? 'Processing...' : 'Confirm & Execute'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIJudgeConfirmationModal; 