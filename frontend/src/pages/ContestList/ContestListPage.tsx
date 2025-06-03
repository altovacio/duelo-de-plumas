import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getContestsWithPagination, Contest as ContestServiceType } from '../../services/contestService';
import { User, searchUsers } from '../../services/userService';
import ContestCard from '../../components/Contest/ContestCard';
import Pagination from '../../components/shared/Pagination';
import { useResponsive } from '../../utils/responsive';

/**
 * ContestListPage - Enhanced with unified search and collapsible filters
 * 
 * Features:
 * - Unified search bar that handles both contest search and creator filtering
 * - Type @username to filter by creator (with autocomplete suggestions)
 * - Collapsible filter panel behind a filter icon
 * - Responsive design using existing mobile/desktop utilities
 * - Visual indicators for active filters
 */

const ContestListPage: React.FC = () => {
  // Data state
  const [displayedContests, setDisplayedContests] = useState<ContestServiceType[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [totalCount, setTotalCount] = useState(0);
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(parseInt(searchParams.get('page') || '1'));
  const [itemsPerPage] = useState(20);
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get('status') || 'all');
  const [typeFilter, setTypeFilter] = useState<string>(searchParams.get('type') || 'all');
  const [deadlineFilter, setDeadlineFilter] = useState<string>(searchParams.get('deadline') || 'all');
  const [sortBy, setSortBy] = useState<string>(searchParams.get('sort') || 'newest');
  const [searchTerm, setSearchTerm] = useState<string>(searchParams.get('search') || '');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isUserFilterActive, setIsUserFilterActive] = useState(false);

  // Unified search state
  const [unifiedSearchTerm, setUnifiedSearchTerm] = useState<string>('');
  const [searchSuggestions, setSearchSuggestions] = useState<User[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearchingUsers, setIsSearchingUsers] = useState(false);

  // Filter dropdown state
  const [showFilters, setShowFilters] = useState(false);

  // Responsive hook
  const { isMobile } = useResponsive();

  // Grouped contests for display
  const [openContests, setOpenContests] = useState<ContestServiceType[]>([]);
  const [evaluationContests, setEvaluationContests] = useState<ContestServiceType[]>([]);
  const [closedContests, setClosedContests] = useState<ContestServiceType[]>([]);

  // Store raw data from server (before client-side filtering)
  const [rawContests, setRawContests] = useState<ContestServiceType[]>([]);

  // Fetch contests with current filters and pagination
  const fetchContests = async () => {
    setIsLoading(true);
    try {
      const skip = (currentPage - 1) * itemsPerPage;
      const contests = await getContestsWithPagination(
        skip,
        itemsPerPage,
        searchTerm.trim() || undefined,
        statusFilter !== 'all' ? statusFilter : undefined,
        isUserFilterActive && selectedUser ? selectedUser.id : undefined,
        undefined, // dateFilter - not used in public page
        undefined  // dateType - not used in public page
      );
      
      // Store raw data for client-side filtering
      setRawContests(contests);
      
      // Estimate total count (backend doesn't return total count yet)
      setTotalCount(contests.length === itemsPerPage ? (currentPage * itemsPerPage) + 1 : skip + contests.length);
    } catch (error) {
      console.error("Error fetching contests:", error);
      setRawContests([]);
      setDisplayedContests([]);
      setOpenContests([]);
      setEvaluationContests([]);
      setClosedContests([]);
    }
    setIsLoading(false);
  };

  // Apply all client-side filtering to raw data
  const applyClientSideFilters = () => {
    if (rawContests.length === 0) {
      setDisplayedContests([]);
      setOpenContests([]);
      setEvaluationContests([]);
      setClosedContests([]);
      return;
    }

    let filteredContests = [...rawContests];
    
    // Apply type filter
    if (typeFilter !== 'all') {
      if (typeFilter === 'private') {
        filteredContests = filteredContests.filter(contest => contest.password_protected || !contest.publicly_listed);
      } else {
        filteredContests = filteredContests.filter(contest => !contest.password_protected && contest.publicly_listed);
      }
    }
    
    // Apply deadline filter
    if (deadlineFilter !== 'all') {
      const now = new Date();
      filteredContests = filteredContests.filter(contest => {
        if (!contest.end_date) {
          // No deadline contests are considered "not expired"
          return deadlineFilter === 'not-expired';
        }
        const deadline = new Date(contest.end_date);
        const isExpired = now > deadline;
        
        return deadlineFilter === 'expired' ? isExpired : !isExpired;
      });
    }
    
    // Apply sorting
    filteredContests.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          // Put expired contests at the bottom, sort newest first within each group
          const nowForNewest = new Date();
          const aExpiredForNewest = a.end_date && nowForNewest > new Date(a.end_date);
          const bExpiredForNewest = b.end_date && nowForNewest > new Date(b.end_date);
          
          // Non-expired before expired
          if (!aExpiredForNewest && bExpiredForNewest) return -1;
          if (aExpiredForNewest && !bExpiredForNewest) return 1;
          
          // Within same expiration status, sort by newest first
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        case 'oldest':
          return new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
        case 'participants-high':
          return (b.participant_count || 0) - (a.participant_count || 0);
        case 'participants-low':
          return (a.participant_count || 0) - (b.participant_count || 0);
        case 'title-az':
          return a.title.localeCompare(b.title);
        case 'title-za':
          return b.title.localeCompare(a.title);
        case 'expiration':
          // Order: Non-expired with deadlines, no deadline, expired
          const now = new Date();
          const aHasDeadline = !!a.end_date;
          const bHasDeadline = !!b.end_date;
          
          if (!aHasDeadline && !bHasDeadline) return 0; // Both no deadline
          
          // If only one has no deadline, handle separately
          if (!aHasDeadline || !bHasDeadline) {
            const aDeadline = aHasDeadline ? new Date(a.end_date!) : null;
            const bDeadline = bHasDeadline ? new Date(b.end_date!) : null;
            
            const aExpired = aDeadline ? now > aDeadline : false;
            const bExpired = bDeadline ? now > bDeadline : false;
            
            // Non-expired with deadline comes first
            if (aDeadline && !aExpired && !bHasDeadline) return -1;
            if (bDeadline && !bExpired && !aHasDeadline) return 1;
            
            // No deadline comes before expired
            if (!aHasDeadline && bExpired) return -1;
            if (!bHasDeadline && aExpired) return 1;
            
            // Both are no deadline or both are expired
            return 0;
          }
          
          // Both have deadlines
          const aDeadline = new Date(a.end_date!);
          const bDeadline = new Date(b.end_date!);
          const aExpired = now > aDeadline;
          const bExpired = now > bDeadline;
          
          // Non-expired before expired
          if (!aExpired && bExpired) return -1;
          if (aExpired && !bExpired) return 1;
          
          // Both expired or both not expired - sort by deadline
          if (!aExpired && !bExpired) {
            // Not expired: closest deadline first
            return aDeadline.getTime() - bDeadline.getTime();
          } else {
            // Both expired: most recently expired first
            return bDeadline.getTime() - aDeadline.getTime();
          }
        default:
          return 0;
      }
    });
    
    setDisplayedContests(filteredContests);
    
    // Group contests by status for display
    setOpenContests(filteredContests.filter(contest => contest.status === 'open'));
    setEvaluationContests(filteredContests.filter(contest => contest.status === 'evaluation'));
    setClosedContests(filteredContests.filter(contest => contest.status === 'closed'));
  };

  // Fetch contests whenever server-side filters or pagination change
  useEffect(() => {
    fetchContests();
  }, [currentPage, searchTerm, statusFilter, selectedUser, isUserFilterActive]);

  // Apply client-side filtering whenever filters change or when raw data updates
  useEffect(() => {
    applyClientSideFilters();
  }, [rawContests, typeFilter, deadlineFilter, sortBy]);

  // Update URL search params
  useEffect(() => {
    const params: Record<string, string> = {};
    if (statusFilter !== 'all') params.status = statusFilter;
    if (typeFilter !== 'all') params.type = typeFilter;
    if (deadlineFilter !== 'all') params.deadline = deadlineFilter;
    if (sortBy !== 'newest') params.sort = sortBy;
    if (searchTerm) params.search = searchTerm;
    if (currentPage > 1) params.page = currentPage.toString();
    
    setSearchParams(params, { replace: true });
  }, [statusFilter, typeFilter, deadlineFilter, sortBy, searchTerm, currentPage, setSearchParams]);

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Handle unified search (both contest content and creator)
  const handleUnifiedSearchChange = async (value: string) => {
    setUnifiedSearchTerm(value);
    
    // If searching for users (starts with @)
    if (value.startsWith('@') && value.length > 1) {
      setIsSearchingUsers(true);
      try {
        const users = await searchUsers(value.substring(1));
        setSearchSuggestions(users);
        setShowSuggestions(true);
      } catch (error) {
        console.error('Error searching users:', error);
        setSearchSuggestions([]);
      }
      setIsSearchingUsers(false);
    } else {
      setShowSuggestions(false);
      setSearchSuggestions([]);
    }

    // Handle regular search or creator filter
    if (value.startsWith('@')) {
      // Creator search mode - don't update contest search yet
      setSearchTerm('');
    } else {
      // Regular contest search
      setSearchTerm(value);
      setSelectedUser(null);
      setIsUserFilterActive(false);
    }
    
    setCurrentPage(1);
  };

  // Handle user selection from suggestions
  const handleUserSelection = (user: User) => {
    setSelectedUser(user);
    setIsUserFilterActive(true);
    setUnifiedSearchTerm(`@${user.username}`);
    setShowSuggestions(false);
    setSearchTerm(''); // Clear contest search when filtering by user
    setCurrentPage(1);
  };

  // Clear search/filter
  const handleClearSearch = () => {
    setUnifiedSearchTerm('');
    setSearchTerm('');
    setSelectedUser(null);
    setIsUserFilterActive(false);
    setShowSuggestions(false);
    setSearchSuggestions([]);
    setCurrentPage(1);
  };

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value);
    setCurrentPage(1);
  };

  const handleTypeFilterChange = (value: string) => {
    setTypeFilter(value);
    setCurrentPage(1);
  };

  const handleSortChange = (value: string) => {
    setSortBy(value);
    setCurrentPage(1);
  };

  const handleDeadlineFilterChange = (value: string) => {
    setDeadlineFilter(value);
    setCurrentPage(1);
  };

  // Contest Section component for each status group
  const ContestSection = ({ 
    title, 
    contests 
  }: { 
    title: string; 
    contests: ContestServiceType[];
  }) => {
    if (contests.length === 0) return null;
    
    return (
      <div className="mb-10">
        <h2 className="text-xl font-semibold mb-4">{title}</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {contests.map(contest => (
            <ContestCard key={contest.id} contest={contest} />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Literary Contests</h1>
        <p className="text-gray-600">Browse all available contests and find one to participate in.</p>
      </div>
      
      {/* Unified Search and Filters */}
      <div className="bg-gray-50 p-4 rounded-lg mb-6">
        <div className="flex flex-col gap-4">
          {/* Search bar row */}
          <div className="flex gap-2">
            <div className="flex-grow relative">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search contests or type @username to filter by creator..."
                  className="w-full px-3 py-2 pr-8 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={unifiedSearchTerm}
                  onChange={(e) => handleUnifiedSearchChange(e.target.value)}
                />
                
                {unifiedSearchTerm && (
                  <button
                    onClick={handleClearSearch}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}

                {isSearchingUsers && (
                  <div className="absolute right-8 top-1/2 transform -translate-y-1/2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                  </div>
                )}
              </div>

              {/* User suggestions dropdown */}
              {showSuggestions && searchSuggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                  {searchSuggestions.map((user) => (
                    <button
                      key={user.id}
                      onClick={() => handleUserSelection(user)}
                      className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                    >
                      <div className="font-medium text-gray-900">@{user.username}</div>
                      {user.email && (
                        <div className="text-sm text-gray-500">{user.email}</div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
            
            {/* Filter toggle button */}
            <div className="relative">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`flex items-center px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors ${
                  showFilters 
                    ? 'bg-indigo-600 text-white border-indigo-600' 
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.707A1 1 0 013 7V4z" />
                </svg>
                {isMobile ? '' : 'Filters'}
              </button>
            </div>
          </div>

          {/* Active filters display */}
          {isUserFilterActive && selectedUser && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-600">Filtering by creator:</span>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                @{selectedUser.username}
                <button
                  onClick={handleClearSearch}
                  className="ml-1 text-indigo-600 hover:text-indigo-800"
                >
                  <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </span>
            </div>
          )}

          {/* Collapsible filter dropdowns */}
          {showFilters && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-gray-200">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
                <select 
                  className="w-full px-3 py-2 text-sm border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={statusFilter}
                  onChange={(e) => handleStatusFilterChange(e.target.value)}
                >
                  <option value="all">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="evaluation">In Evaluation</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
                <select 
                  className="w-full px-3 py-2 text-sm border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={typeFilter}
                  onChange={(e) => handleTypeFilterChange(e.target.value)}
                >
                  <option value="all">All Types</option>
                  <option value="public">Public</option>
                  <option value="private">Private</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Deadline</label>
                <select 
                  className="w-full px-3 py-2 text-sm border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={deadlineFilter}
                  onChange={(e) => handleDeadlineFilterChange(e.target.value)}
                >
                  <option value="all">All Deadlines</option>
                  <option value="not-expired">Not Expired</option>
                  <option value="expired">Expired</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Sort By</label>
                <select 
                  className="w-full px-3 py-2 text-sm border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={sortBy}
                  onChange={(e) => handleSortChange(e.target.value)}
                >
                  <option value="newest">Newest First</option>
                  <option value="oldest">Oldest First</option>
                  <option value="expiration">By Expiration</option>
                  <option value="participants-high">Most Participants</option>
                  <option value="participants-low">Fewest Participants</option>
                  <option value="title-az">Title A-Z</option>
                  <option value="title-za">Title Z-A</option>
                </select>
              </div>
            </div>
          )}

          {/* Results count */}
          <div className="text-sm text-gray-500">
            Showing {displayedContests.length} contests
            {totalCount > itemsPerPage && ` (page ${currentPage})`}
          </div>
        </div>
      </div>
      
      {/* Contest listing */}
      {isLoading ? (
        <div className="text-center py-16">
          <div className="flex justify-center items-center">
            <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <p className="text-gray-500 mt-2">Loading contests...</p>
        </div>
      ) : displayedContests.length === 0 ? (
        <div className="text-center py-16 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No contests found matching your criteria.</p>
        </div>
      ) : (
        <div>
          <ContestSection 
            title="Open Contests" 
            contests={openContests} 
          />
          
          <ContestSection 
            title="Contests in Evaluation" 
            contests={evaluationContests} 
          />
          
          <ContestSection 
            title="Closed Contests" 
            contests={closedContests} 
          />
        </div>
      )}
      
      {/* Pagination */}
      {!isLoading && totalCount > itemsPerPage && (
        <Pagination
          currentPage={currentPage}
          totalItems={totalCount}
          itemsPerPage={itemsPerPage}
          onPageChange={handlePageChange}
          className="mt-8"
        />
      )}
    </div>
  );
};

export default ContestListPage; 