import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import BackButton from '../../components/ui/BackButton';
import { deleteUserByAdmin, getAdminUsersWithCounts, User } from '../../services/userService';
import { updateUserCredits } from '../../services/creditService';
import Pagination from '../../components/shared/Pagination';
import AdminUserSearch from '../../components/shared/AdminUserSearch';

const formatLastLogin = (lastLogin: string): string => {
  if (!lastLogin) return 'Never';
  return new Date(lastLogin).toLocaleDateString();
};

const AdminUsersPage: React.FC = () => {
  // Data state
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const [itemsPerPage] = useState(25);
  
  // Search state
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isSearchMode, setIsSearchMode] = useState(false);
  
  // Modal state
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [isCreditModalOpen, setIsCreditModalOpen] = useState(false);
  const [userToModifyCredits, setUserToModifyCredits] = useState<User | null>(null);
  const [creditAmount, setCreditAmount] = useState<number>(0);

  // Fetch users with pagination or search - OPTIMIZED VERSION
  const fetchUsers = async (page: number = 1, searchUser: User | null = null) => {
    setIsLoading(true);
    try {
      const skipAmount = (page - 1) * itemsPerPage;
      let fetchedUsers: User[];
      
      if (searchUser) {
        // Search mode - get specific user with contest count (estimated)
        fetchedUsers = [{
          ...searchUser,
          contests_created: searchUser.contests_created || 0
        }];
        setTotalUsers(1);
        setIsSearchMode(true);
      } else {
        // Normal pagination mode - get all users WITH contest counts in single query
        fetchedUsers = await getAdminUsersWithCounts(skipAmount, itemsPerPage);
        
        // For now, we'll use a simple approach to estimate total count
        // In a real app, the API should return total count
        if (fetchedUsers.length < itemsPerPage) {
          setTotalUsers(skipAmount + fetchedUsers.length);
        } else {
          // Estimate: if we got a full page, there might be more
          setTotalUsers(skipAmount + itemsPerPage + 1);
        }
        setIsSearchMode(false);
      }
      
      // No need to process users anymore - contest counts come from the API!
      setUsers(fetchedUsers);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users. Check console for details.');
    } finally {
      setIsLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchUsers(1);
  }, []);

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    fetchUsers(page, selectedUser);
  };

  // Handle user search selection
  const handleUserSelect = (user: User | null) => {
    setSelectedUser(user);
    setCurrentPage(1);
    fetchUsers(1, user);
  };

  // Handle clearing search
  const handleClearSearch = () => {
    setSelectedUser(null);
    setCurrentPage(1);
    fetchUsers(1, null);
  };

  const handleModifyCredits = async () => {
    if (!userToModifyCredits || creditAmount === 0) return;

    try {
      const description = creditAmount > 0 
        ? `Admin added ${creditAmount} credits` 
        : `Admin deducted ${Math.abs(creditAmount)} credits`;
      
      await updateUserCredits(userToModifyCredits.id, creditAmount, description);
      
      // Update local state
      setUsers(users.map(user => 
        user.id === userToModifyCredits.id 
          ? { ...user, credits: (user.credits || 0) + creditAmount } 
          : user
      ));
      
      toast.success(`Credits ${creditAmount > 0 ? 'added' : 'removed'} successfully`);
      
      // Close modal regardless of success/failure
      setIsCreditModalOpen(false);
      setUserToModifyCredits(null);
      setCreditAmount(0);
    } catch (error: any) {
      console.error('Error modifying credits:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to modify credits. Please check the server logs.';
      toast.error(errorMessage);
      // Keep modal open to let user try again
    }
  };

  const handleDeleteUser = async () => {
    if (!userToDelete) return;

    try {
      await deleteUserByAdmin(userToDelete.id);
      
      // Update local state
      setUsers(users.filter(user => user.id !== userToDelete.id));
      
      toast.success('User deleted successfully');
      setIsDeleteModalOpen(false);
      setUserToDelete(null);
      
      // If we deleted the only user on this page, go back a page
      if (users.length === 1 && currentPage > 1) {
        handlePageChange(currentPage - 1);
      } else {
        // Refresh current page
        fetchUsers(currentPage, selectedUser);
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error('Failed to delete user. Check console for details.');
    }
  };

  const openCreditModal = (user: User) => {
    setUserToModifyCredits(user);
    setCreditAmount(0);
    setIsCreditModalOpen(true);
  };

  const openDeleteModal = (user: User) => {
    setUserToDelete(user);
    setIsDeleteModalOpen(true);
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center">
          <BackButton to="/admin" label="Back to Dashboard" />
          <h1 className="text-3xl font-bold ml-4">User Management</h1>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Users</h2>
            <div className="flex items-center space-x-4">
              {isSearchMode && (
                <button
                  onClick={handleClearSearch}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200"
                >
                  Clear Search
                </button>
              )}
              <div className="w-80">
                <AdminUserSearch
                  onUserSelect={handleUserSelect}
                  placeholder="Search users by username or email..."
                  selectedUser={selectedUser}
                />
              </div>
            </div>
          </div>
          {isSearchMode && selectedUser && (
            <div className="mt-2 text-sm text-gray-600">
              Showing results for: <span className="font-medium">{selectedUser.username}</span>
            </div>
          )}
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
                    Username
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Credits
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contests Created
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Joined
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Login
                  </th>
                  <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.length > 0 ? (
                  users.map((user) => (
                    <tr key={user.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-gray-900">{user.username}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-gray-500">{user.email || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          user.is_admin ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'
                        }`}>
                          {user.is_admin ? 'Admin' : 'User'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {user.credits || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {typeof user.contests_created === 'number' ? user.contests_created : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {user.last_login ? formatLastLogin(user.last_login) : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                        <div className="flex justify-center space-x-2">
                          <button
                            onClick={() => openCreditModal(user)}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            Modify Credits
                          </button>
                          <button
                            onClick={() => openDeleteModal(user)}
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
                    <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                      {isSearchMode ? 'No user found matching your search.' : 'No users found.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Pagination - only show when not in search mode */}
        {!isSearchMode && !isLoading && (
          <Pagination
            currentPage={currentPage}
            totalItems={totalUsers}
            itemsPerPage={itemsPerPage}
            onPageChange={handlePageChange}
          />
        )}
      </div>

      {/* Credit Modification Modal */}
      {isCreditModalOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Modify Credits for {userToModifyCredits?.username}
              </h3>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Credit Amount (positive to add, negative to remove)
                </label>
                <input
                  type="number"
                  value={creditAmount}
                  onChange={(e) => setCreditAmount(parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter credit amount..."
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => {
                    setIsCreditModalOpen(false);
                    setUserToModifyCredits(null);
                    setCreditAmount(0);
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  onClick={handleModifyCredits}
                  disabled={creditAmount === 0}
                  className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Modify Credits
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Delete User
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                Are you sure you want to delete user "{userToDelete?.username}"? This action cannot be undone.
              </p>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => {
                    setIsDeleteModalOpen(false);
                    setUserToDelete(null);
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteUser}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Delete User
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminUsersPage; 