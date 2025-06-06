import React, { useState, useEffect, useRef } from 'react';
import MDEditor from '@uiw/react-md-editor';

interface ContestFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (contest: { 
    title: string; 
    description: string; 
    password_protected: boolean;
    password?: string;
    publicly_listed: boolean;
    end_date?: string;
    judge_restrictions?: boolean;
    author_restrictions?: boolean;
    min_votes_required?: number;
    status?: 'open' | 'evaluation' | 'closed';
  }) => void;
  initialContest?: { 
    title: string; 
    description: string; 
    password_protected: boolean;
    password?: string;
    publicly_listed: boolean;
    end_date?: string;
    judge_restrictions?: boolean;
    author_restrictions?: boolean;
    min_votes_required?: number;
    status?: 'open' | 'evaluation' | 'closed';
  };
  isEditing?: boolean;
}

const ContestFormModal: React.FC<ContestFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialContest = { 
    title: '', 
    description: '', 
    password_protected: false,
    publicly_listed: true,
    judge_restrictions: false,
    author_restrictions: false,
  },
  isEditing = false,
}) => {
  // Helper function to format date for datetime-local input
  const formatDateForInput = (isoString: string | null | undefined): string => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      // Format to YYYY-MM-DDTHH:MM (datetime-local format)
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day}T${hours}:${minutes}`;
    } catch {
      return '';
    }
  };

  // Helper function to format date for API (ISO format)
  const formatDateForAPI = (dateTimeLocal: string): string => {
    if (!dateTimeLocal) return '';
    try {
      const date = new Date(dateTimeLocal);
      return date.toISOString();
    } catch {
      return '';
    }
  };

  // Track if this is the first render or if isOpen changed
  const firstRender = useRef(true);
  const wasOpen = useRef(isOpen);
  
  const [title, setTitle] = useState(initialContest.title);
  const [description, setDescription] = useState(initialContest.description);
  const [passwordProtected, setPasswordProtected] = useState(initialContest.password_protected);
  const [publiclyListed, setPubliclyListed] = useState(initialContest.publicly_listed);
  const [password, setPassword] = useState(initialContest.password || '');
  const [endDate, setEndDate] = useState(formatDateForInput(initialContest.end_date));
  const [judgeRestrictions, setJudgeRestrictions] = useState(initialContest.judge_restrictions || false);
  const [authorRestrictions, setAuthorRestrictions] = useState(initialContest.author_restrictions || false);
  const [minVotesRequired, setMinVotesRequired] = useState<number | undefined>(initialContest.min_votes_required);
  const [status, setStatus] = useState<'open' | 'evaluation' | 'closed' | undefined>(
    isEditing ? initialContest.status : undefined
  );

  // Only update form values when the modal opens or initialContest changes significantly
  useEffect(() => {
    // Only run this effect when modal opens or on first render with initialContest
    if ((isOpen && !wasOpen.current) || firstRender.current) {
      setTitle(initialContest.title);
      setDescription(initialContest.description);
      setPasswordProtected(initialContest.password_protected);
      setPubliclyListed(initialContest.publicly_listed);
      setPassword(initialContest.password || '');
      setEndDate(formatDateForInput(initialContest.end_date));
      setJudgeRestrictions(initialContest.judge_restrictions || false);
      setAuthorRestrictions(initialContest.author_restrictions || false);
      setMinVotesRequired(initialContest.min_votes_required);
      if (isEditing) {
        setStatus(initialContest.status);
      }
      firstRender.current = false;
    }
    
    // Update the ref tracking if modal is open
    wasOpen.current = isOpen;
  }, [isOpen, initialContest, isEditing]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const contestData = {
      title, 
      description, 
      password_protected: passwordProtected,
      password: passwordProtected && password ? password : undefined,
      publicly_listed: publiclyListed,
      end_date: formatDateForAPI(endDate),
      judge_restrictions: judgeRestrictions,
      author_restrictions: authorRestrictions,
      min_votes_required: minVotesRequired,
    };

    // Only include status for editing existing contests
    if (isEditing && status) {
      onSubmit({ ...contestData, status });
    } else {
      onSubmit(contestData);
    }
    
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {isEditing ? 'Edit Contest' : 'Create New Contest'}
                </h3>
              </div>

              <div className="mb-4">
                <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                  Title
                </label>
                <input
                  type="text"
                  id="title"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  placeholder="Enter contest title"
                />
              </div>

              <div className="mb-4">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <div data-color-mode="light">
                  <MDEditor
                    value={description}
                    onChange={(value) => setDescription(value || '')}
                    height={200}
                  />
                </div>
              </div>

              <div className="mb-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">
                    End Date (Optional)
                  </label>
                  <input
                    type="datetime-local"
                    id="end_date"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    If not set, the contest will remain open until manually closed
                  </p>
                </div>

                <div>
                  <label htmlFor="min_votes" className="block text-sm font-medium text-gray-700">
                    Minimum Required Votes
                  </label>
                  <input
                    type="number"
                    id="min_votes"
                    min={0}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    value={minVotesRequired === undefined ? '' : minVotesRequired}
                    onChange={(e) => setMinVotesRequired(e.target.value ? parseInt(e.target.value) : undefined)}
                    placeholder="Default"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Minimum number of texts to be evaluated by each judge
                  </p>
                </div>
              </div>

              <div className="mb-4 space-y-4">
                <div className="flex items-center">
                  <input
                    id="publicly_listed"
                    name="publicly_listed"
                    type="checkbox"
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    checked={publiclyListed}
                    onChange={(e) => setPubliclyListed(e.target.checked)}
                  />
                  <label htmlFor="publicly_listed" className="ml-2 block text-sm text-gray-900">
                    List in public contests
                  </label>
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  If unchecked, only designated members can access this contest.
                </p>

                <div className="flex items-center">
                  <input
                    id="password_protected"
                    name="password_protected"
                    type="checkbox"
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    checked={passwordProtected}
                    onChange={(e) => setPasswordProtected(e.target.checked)}
                  />
                  <label htmlFor="password_protected" className="ml-2 block text-sm text-gray-900">
                    Password protected
                  </label>
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  Require participants to enter a password to join the contest.
                </p>
              </div>

              {passwordProtected && (
                <div className="mb-4">
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                    Password
                  </label>
                  <input
                    type="password"
                    id="password"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required={passwordProtected}
                    placeholder="Enter password for contest"
                  />
                </div>
              )}

              <div className="mb-4 space-y-2">
                <div className="flex items-center">
                  <input
                    id="judge_restrictions"
                    name="judge_restrictions"
                    type="checkbox"
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    checked={judgeRestrictions}
                    onChange={(e) => setJudgeRestrictions(e.target.checked)}
                  />
                  <label htmlFor="judge_restrictions" className="ml-2 block text-sm text-gray-900">
                    Prevent judges from participating as authors
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    id="author_restrictions"
                    name="author_restrictions"
                    type="checkbox"
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    checked={authorRestrictions}
                    onChange={(e) => setAuthorRestrictions(e.target.checked)}
                  />
                  <label htmlFor="author_restrictions" className="ml-2 block text-sm text-gray-900">
                    Limit authors to one submission
                  </label>
                </div>
              </div>

              {isEditing && (
                <div className="mb-4">
                  <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                    Contest Status
                  </label>
                  <select
                    id="status"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    value={status}
                    onChange={(e) => setStatus(e.target.value as 'open' | 'evaluation' | 'closed')}
                  >
                    <option value="open">Open (accepting submissions)</option>
                    <option value="evaluation">Evaluation (judging in progress)</option>
                    <option value="closed">Closed (final results published)</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    Changing status to 'evaluation' will lock submissions. Changing to 'closed' will reveal results and participant identities.
                  </p>
                </div>
              )}
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
              >
                {isEditing ? 'Save Changes' : 'Create Contest'}
              </button>
              <button
                type="button"
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                onClick={onClose}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ContestFormModal; 