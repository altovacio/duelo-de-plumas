import React, { useState, useEffect } from 'react';
import { searchAdminUsers, User } from '../../services/userService';

interface AdminUserSearchProps {
  onUserSelect: (user: User | null) => void;
  placeholder?: string;
  className?: string;
  selectedUser?: User | null;
}

const AdminUserSearch: React.FC<AdminUserSearchProps> = ({
  onUserSelect,
  placeholder = "Search users by username or email...",
  className = "",
  selectedUser = null
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  // Debounced search effect
  useEffect(() => {
    const timeoutId = setTimeout(async () => {
      if (searchTerm.trim().length >= 2) {
        setIsSearching(true);
        try {
          const results = await searchAdminUsers(searchTerm.trim(), 0, 10);
          setSearchResults(results);
          setShowResults(true);
        } catch (error) {
          console.error('Error searching users:', error);
          setSearchResults([]);
        } finally {
          setIsSearching(false);
        }
      } else {
        setSearchResults([]);
        setShowResults(false);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  const handleUserClick = (user: User) => {
    onUserSelect(user);
    setSearchTerm(user.username);
    setSearchResults([]);
    setShowResults(false);
  };

  const handleClearSelection = () => {
    onUserSelect(null);
    setSearchTerm('');
    setSearchResults([]);
    setShowResults(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    
    // If user clears the search term, also clear the selection
    if (value === '' && selectedUser) {
      onUserSelect(null);
    }
  };

  const handleInputBlur = () => {
    // Delay hiding results to allow for clicks
    setTimeout(() => setShowResults(false), 200);
  };

  const handleInputFocus = () => {
    if (searchResults.length > 0 && searchTerm.length >= 2) {
      setShowResults(true);
    }
  };

  // Set initial value if selectedUser is provided
  useEffect(() => {
    if (selectedUser && !searchTerm) {
      setSearchTerm(selectedUser.username);
    }
  }, [selectedUser]);

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <input
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          onFocus={handleInputFocus}
          placeholder={placeholder}
          className="w-full px-3 py-2 pr-8 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
        
        {selectedUser && searchTerm && (
          <button
            onClick={handleClearSelection}
            className="absolute right-8 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
        
        {isSearching && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
          </div>
        )}
      </div>

      {showResults && searchResults.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
          {searchResults.map((user) => (
            <button
              key={user.id}
              onClick={() => handleUserClick(user)}
              className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none border-b border-gray-100 last:border-b-0"
            >
              <div className="font-medium text-gray-900">{user.username}</div>
              {user.email && (
                <div className="text-sm text-gray-500">{user.email}</div>
              )}
            </button>
          ))}
        </div>
      )}

      {showResults && searchResults.length === 0 && searchTerm.length >= 2 && !isSearching && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
          <div className="px-4 py-2 text-gray-500 text-sm">
            No users found matching "{searchTerm}"
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminUserSearch; 