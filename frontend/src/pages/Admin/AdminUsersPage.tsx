import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import BackButton from '../../components/ui/BackButton';
import { deleteUserByAdmin, getAdminUsers } from '../../services/userService';
import { updateUserCredits } from '../../services/creditService';
import { getContests } from '../../services/contestService';

// Updated User interface for more comprehensive user details, especially for admin views
export interface User {
  id: number;
  username: string;
  email?: string; // Assuming email is available
  is_admin?: boolean;
  credits?: number; // For admin views
  created_at?: string;
  last_login?: string | null; // For admin views - tracks when user last logged in
  contests_created?: number | string; // For admin views, can be N/A when there's an error
  // Add other fields as returned by GET /admin/users
}

// mockUsers removed
// const mockUsers: User[] = [ ... ];

// Mock function to assign credits to a user
const modifyUserCredits = async (userId: number, amount: number) => {
  try {
    // Call the proper API with a descriptive message
    const description = amount > 0 
      ? `Admin added ${amount} credits` 
      : `Admin deducted ${Math.abs(amount)} credits`;
    
    await updateUserCredits(userId, amount, description);
    return { success: true };
  } catch (error) {
    console.error("Error modifying user credits:", error);
    throw error; // Re-throw to be handled by the caller
  }
};

// Helper function to format last login time
const formatLastLogin = (lastLogin: string | null) => {
  if (!lastLogin) return 'Never';
  
  const loginDate = new Date(lastLogin);
  const now = new Date();
  const diffInMs = now.getTime() - loginDate.getTime();
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  
  if (diffInMinutes < 60) {
    return diffInMinutes <= 1 ? 'Just now' : `${diffInMinutes} minutes ago`;
  } else if (diffInHours < 24) {
    return diffInHours === 1 ? '1 hour ago' : `${diffInHours} hours ago`;
  } else if (diffInDays < 7) {
    return diffInDays === 1 ? '1 day ago' : `${diffInDays} days ago`;
  } else {
    return loginDate.toLocaleDateString();
  }
};

const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [isCreditModalOpen, setIsCreditModalOpen] = useState(false);
  const [userToModifyCredits, setUserToModifyCredits] = useState<User | null>(null);
  const [creditAmount, setCreditAmount] = useState<number>(0);

  useEffect(() => {
    const fetchUsers = async () => {
      setIsLoading(true);
      try {
        // Fetch real user data
        const fetchedUsers = await getAdminUsers();
        
        // Process users sequentially to avoid overwhelming the server
        const processedUsers = [...fetchedUsers];
        
        for (let i = 0; i < fetchedUsers.length; i++) {
          const user = fetchedUsers[i];
          try {
            // Add a small delay between requests to avoid overwhelming the server
            if (i > 0) {
              await new Promise(resolve => setTimeout(resolve, 100));
            }
            
            // Use contestService to get contests created by this user
            const userContests = await getContests({ creator: user.id.toString() });
            processedUsers[i] = { ...user, contests_created: userContests.length };
          } catch (error) {
            console.error(`Error fetching contests for user ${user.id}:`, error);
            processedUsers[i] = { ...user, contests_created: 'N/A' };
          }
        }
        
        setUsers(processedUsers);
      } catch (error) {
        console.error('Error fetching users:', error);
        toast.error('Failed to load users. Check console for details.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsers();
  }, []);

  const handleModifyCredits = async () => {
    if (!userToModifyCredits || creditAmount === 0) return;

    try {
      await modifyUserCredits(userToModifyCredits.id, creditAmount);
      
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

  const filteredUsers = users.filter(user => 
    user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (user.email || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

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
          <div className="flex items-center">
            <h2 className="text-xl font-semibold mr-4">Users</h2>
            <div className="flex-grow">
              <input
                type="text"
                placeholder="Search users..."
                className="w-full px-3 py-2 border rounded-lg"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
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
                {filteredUsers.length > 0 ? (
                  filteredUsers.map((user) => (
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
                      No users found matching your search.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Credit Modification Modal */}
      {isCreditModalOpen && userToModifyCredits && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-bold mb-4">Modify Credits for {userToModifyCredits.username}</h3>
            <p className="mb-4">Current balance: <span className="font-bold">{userToModifyCredits.credits || 0}</span> credits</p>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Credit Amount (use negative values to deduct)
              </label>
              <input 
                type="number" 
                className="w-full px-3 py-2 border rounded-lg"
                value={creditAmount}
                onChange={(e) => setCreditAmount(Number(e.target.value))}
              />
              <p className="text-sm text-gray-500 mt-1">
                New balance will be: {(userToModifyCredits.credits || 0) + creditAmount}
              </p>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setIsCreditModalOpen(false)}
                className="px-4 py-2 border rounded-md hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={handleModifyCredits}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                disabled={creditAmount === 0}
              >
                {creditAmount > 0 ? 'Add Credits' : creditAmount < 0 ? 'Deduct Credits' : 'No Change'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete User Modal */}
      {isDeleteModalOpen && userToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-bold mb-4">Delete User</h3>
            <p className="mb-4">
              Are you sure you want to delete the user <span className="font-bold">{userToDelete.username}</span>?
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
                onClick={handleDeleteUser}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Delete User
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminUsersPage; 