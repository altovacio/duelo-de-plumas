import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { getContests, Contest, deleteContest as deleteContestService, updateContest } from '../../services/contestService';
import BackButton from '../../components/ui/BackButton';
import ContestFormModal from '../../components/Contest/ContestFormModal';

// Mock functions for edit and delete
// const deleteContest = async (id: number) => { ... };

const AdminContestsPage: React.FC = () => {
  const [contests, setContests] = useState<Contest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [dateFilter, setDateFilter] = useState<string>('all');
  const [dateType, setDateType] = useState<string>('created');
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [contestToDelete, setContestToDelete] = useState<Contest | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [contestToEdit, setContestToEdit] = useState<Contest | null>(null);

  useEffect(() => {
    const fetchContests = async () => {
      setIsLoading(true);
      try {
        const allContests = await getContests({});
        setContests(allContests);
      } catch (error) {
        console.error('Error fetching contests:', error);
        toast.error('Failed to load contests');
      } finally {
        setIsLoading(false);
      }
    };

    fetchContests();
  }, []);

  const handleDeleteContest = async () => {
    if (!contestToDelete) return;

    try {
      // Use the imported service function
      await deleteContestService(contestToDelete.id);
      
      // Update local state
      setContests(contests.filter(contest => contest.id !== contestToDelete.id));
      
      toast.success('Contest deleted successfully');
      setIsDeleteModalOpen(false);
      setContestToDelete(null);
    } catch (error) {
      console.error('Error deleting contest:', error);
      toast.error('Failed to delete contest. Check console for details.');
    }
  };

  const openDeleteModal = (contest: Contest) => {
    setContestToDelete(contest);
    setIsDeleteModalOpen(true);
  };

  const openEditModal = (contest: Contest) => {
    setContestToEdit(contest);
    setIsEditModalOpen(true);
  };

  const handleContestUpdated = (updatedContest: Contest) => {
    setContests(contests.map(contest => 
      contest.id === updatedContest.id ? updatedContest : contest
    ));
  };

  const handleContestSubmit = async (contestData: any) => {
    try {
      const updatedContest = await updateContest(contestToEdit!.id, contestData);
      handleContestUpdated(updatedContest);
      setIsEditModalOpen(false);
      toast.success('Contest updated successfully');
    } catch (error) {
      console.error('Error updating contest:', error);
      toast.error('Failed to update contest');
    }
  };

  // Filter contests based on search query, status filter, and date filter
  const filteredContests = contests.filter(contest => {
    // Search filter
    const matchesSearch = 
      contest.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      contest.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    // Status filter
    const matchesStatus = 
      statusFilter === 'all' || 
      contest.status === statusFilter;
    
    // Date filter
    if (dateFilter !== 'all') {
      const contestDate = dateType === 'created' 
        ? new Date(contest.created_at) 
        : new Date(contest.updated_at);
      
      if (dateFilter === 'last7days') {
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        if (contestDate < sevenDaysAgo) {
          return false;
        }
      } else if (dateFilter === 'last30days') {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        if (contestDate < thirtyDaysAgo) {
          return false;
        }
      } else if (dateFilter === 'last365days') {
        const yearAgo = new Date();
        yearAgo.setFullYear(yearAgo.getFullYear() - 1);
        if (contestDate < yearAgo) {
          return false;
        }
      }
    }
    
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center">
          <BackButton to="/admin" label="Back to Dashboard" />
          <h1 className="text-3xl font-bold ml-4">Contests Oversight</h1>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              placeholder="Search by title or description..."
              className="w-full px-3 py-2 border rounded-lg"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              className="w-full px-3 py-2 border rounded-lg"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="open">Open</option>
              <option value="evaluation">Evaluation</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date Range
            </label>
            <select
              className="w-full px-3 py-2 border rounded-lg"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
            >
              <option value="all">All Time</option>
              <option value="last7days">Last 7 Days</option>
              <option value="last30days">Last 30 Days</option>
              <option value="last365days">Last Year</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date Type
            </label>
            <select
              className="w-full px-3 py-2 border rounded-lg"
              value={dateType}
              onChange={(e) => setDateType(e.target.value)}
            >
              <option value="created">Created Date</option>
              <option value="updated">Last Updated</option>
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">All Contests</h2>
        </div>
        
        {isLoading ? (
          <div className="flex justify-center items-center h-32">
            <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Creator
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Participants
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Texts
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Updated
                  </th>
                  <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredContests.length > 0 ? (
                  filteredContests.map((contest) => (
                    <tr key={contest.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link 
                          to={`/contests/${contest.id}`}
                          className="font-medium text-indigo-600 hover:text-indigo-900 hover:underline"
                        >
                          {contest.title}
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          contest.status === 'open' ? 'bg-green-100 text-green-800' :
                          contest.status === 'evaluation' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {contest.status.charAt(0).toUpperCase() + contest.status.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          (contest.password_protected || !contest.publicly_listed) ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {(contest.password_protected || !contest.publicly_listed) ? 'Private' : 'Public'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {contest.creator?.username || `User #${contest.creator?.id || 'Unknown'}`}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {contest.participant_count || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {contest.text_count || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(contest.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(contest.updated_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                        <div className="flex justify-center space-x-2">
                          <Link 
                            to={`/contests/${contest.id}`}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            View
                          </Link>
                          <button 
                            onClick={() => openEditModal(contest)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => openDeleteModal(contest)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="px-6 py-4 text-center text-gray-500">
                      No contests found matching your criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Contest Modal */}
      {isDeleteModalOpen && contestToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-bold mb-4">Delete Contest</h3>
            <p className="mb-4">
              Are you sure you want to delete the contest <span className="font-bold">{contestToDelete.title}</span>?
              This action cannot be undone.
            </p>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setIsDeleteModalOpen(false)}
                className="px-4 py-2 border rounded-md hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteContest}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Delete Contest
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Contest Modal */}
      {contestToEdit && (
        <ContestFormModal
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          onSubmit={handleContestSubmit}
          initialContest={{
            title: contestToEdit.title,
            description: contestToEdit.description,
            password_protected: contestToEdit.password_protected,
            publicly_listed: contestToEdit.publicly_listed,
            password: contestToEdit.password || undefined,
            end_date: contestToEdit.end_date || undefined,
            judge_restrictions: contestToEdit.judge_restrictions,
            author_restrictions: contestToEdit.author_restrictions,
            min_votes_required: contestToEdit.min_votes_required,
            status: contestToEdit.status,
          }}
          isEditing={true}
        />
      )}
    </div>
  );
};

export default AdminContestsPage; 