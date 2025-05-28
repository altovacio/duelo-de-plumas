import React, { useState, useEffect } from 'react';
import { Contest, updateContest } from '../../services/contestService';
import { toast } from 'react-hot-toast';

interface ContestEditModalProps {
  contest: Contest;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (updatedContest: Contest) => void;
}

const ContestEditModal: React.FC<ContestEditModalProps> = ({ 
  contest, 
  isOpen, 
  onClose,
  onSuccess 
}) => {
  // Form state
  const [title, setTitle] = useState(contest.title);
  const [description, setDescription] = useState(contest.description);
  const [passwordProtected, setPasswordProtected] = useState(contest.password_protected);
  const [publiclyListed, setPubliclyListed] = useState(contest.publicly_listed);
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState(contest.status);
  const [startDate, setStartDate] = useState(contest.start_date || '');
  const [endDate, setEndDate] = useState(contest.end_date || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Reset form when contest changes
  useEffect(() => {
    if (isOpen) {
      setTitle(contest.title);
      setDescription(contest.description);
      setPasswordProtected(contest.password_protected);
      setPubliclyListed(contest.publicly_listed);
      setPassword('');
      setStatus(contest.status);
      setStartDate(contest.start_date || '');
      setEndDate(contest.end_date || '');
      setErrors({});
    }
  }, [contest, isOpen]);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    const validationErrors: Record<string, string> = {};
    
    if (!title.trim()) {
      validationErrors.title = 'Title is required';
    }
    
    if (!description.trim()) {
      validationErrors.description = 'Description is required';
    }
    
    if (passwordProtected && !contest.has_password && !password.trim()) {
      validationErrors.password = 'Password is required for password-protected contests';
    }
    
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Prepare contest data
      const contestData: Partial<Contest> = {
        title,
        description,
        password_protected: passwordProtected,
        publicly_listed: publiclyListed,
        status,
      };
      
      // Only include password if it's changed
      if (password.trim()) {
        contestData.password = password;
      }
      
      // Only include dates if they've been set
      if (startDate) {
        contestData.start_date = startDate;
      }
      
      if (endDate) {
        contestData.end_date = endDate;
      }
      
      // Update contest
      const updatedContest = await updateContest(contest.id, contestData);
      
      toast.success('Contest updated successfully');
      
      // Call onSuccess callback if provided
      if (onSuccess) {
        onSuccess(updatedContest);
      }
      
      onClose();
    } catch (error) {
      console.error('Error updating contest:', error);
      toast.error('Failed to update contest');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Edit Contest</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
              Title
            </label>
            <input
              type="text"
              id="title"
              className={`w-full px-3 py-2 border rounded-lg ${errors.title ? 'border-red-500' : 'border-gray-300'}`}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            {errors.title && <p className="mt-1 text-sm text-red-500">{errors.title}</p>}
          </div>

          <div className="mb-4">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              className={`w-full px-3 py-2 border rounded-lg ${errors.description ? 'border-red-500' : 'border-gray-300'}`}
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            {errors.description && <p className="mt-1 text-sm text-red-500">{errors.description}</p>}
          </div>

          <div className="mb-4">
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              id="status"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              value={status}
              onChange={(e) => setStatus(e.target.value as 'open' | 'evaluation' | 'closed')}
            >
              <option value="open">Open</option>
              <option value="evaluation">Evaluation</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Visibility Settings
            </label>
            
            <div className="space-y-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="publiclyListed"
                  className="mr-2"
                  checked={publiclyListed}
                  onChange={(e) => setPubliclyListed(e.target.checked)}
                />
                <label htmlFor="publiclyListed" className="text-sm">
                  Publicly listed (appears in contest listings)
                </label>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="passwordProtected"
                  className="mr-2"
                  checked={passwordProtected}
                  onChange={(e) => setPasswordProtected(e.target.checked)}
                />
                <label htmlFor="passwordProtected" className="text-sm">
                  Password protected (requires password to access)
                </label>
              </div>
            </div>
            
            <div className="mt-2 text-xs text-gray-600">
              <p>• Publicly listed + No password = Public contest</p>
              <p>• Publicly listed + Password = Listed but requires password</p>
              <p>• Not publicly listed = Private contest (invite-only)</p>
            </div>
          </div>

          {passwordProtected && (
            <div className="mb-4">
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                {contest.has_password ? 'Change Password (leave blank to keep current)' : 'Password'}
              </label>
              <input
                type="password"
                id="password"
                className={`w-full px-3 py-2 border rounded-lg ${errors.password ? 'border-red-500' : 'border-gray-300'}`}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={contest.has_password ? '••••••••' : 'Enter password'}
              />
              {errors.password && <p className="mt-1 text-sm text-red-500">{errors.password}</p>}
            </div>
          )}

          <div className="mb-4">
            <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-1">
              Start Date (optional)
            </label>
            <input
              type="datetime-local"
              id="startDate"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              value={startDate ? new Date(startDate).toISOString().slice(0, 16) : ''}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div className="mb-6">
            <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 mb-1">
              End Date (optional)
            </label>
            <input
              type="datetime-local"
              id="endDate"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              value={endDate ? new Date(endDate).toISOString().slice(0, 16) : ''}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-100"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-indigo-300"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ContestEditModal; 