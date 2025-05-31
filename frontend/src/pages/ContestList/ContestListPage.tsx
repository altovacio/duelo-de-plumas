import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getContestsWithPagination, Contest as ContestServiceType } from '../../services/contestService';
import { User } from '../../services/userService';
import ContestCard from '../../components/Contest/ContestCard';
import Pagination from '../../components/shared/Pagination';
import UserSearch from '../../components/shared/UserSearch';

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
  const [sortBy, setSortBy] = useState<string>(searchParams.get('sort') || 'newest');
  const [searchTerm, setSearchTerm] = useState<string>(searchParams.get('search') || '');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isUserFilterActive, setIsUserFilterActive] = useState(false);

  // Grouped contests for display
  const [openContests, setOpenContests] = useState<ContestServiceType[]>([]);
  const [evaluationContests, setEvaluationContests] = useState<ContestServiceType[]>([]);
  const [closedContests, setClosedContests] = useState<ContestServiceType[]>([]);

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
      
      // Apply client-side filtering for type and sorting since backend doesn't support these yet
      let filteredContests = [...contests];
      
      // Apply type filter
      if (typeFilter !== 'all') {
        if (typeFilter === 'private') {
          filteredContests = filteredContests.filter(contest => contest.password_protected || !contest.publicly_listed);
        } else {
          filteredContests = filteredContests.filter(contest => !contest.password_protected && contest.publicly_listed);
        }
      }
      
      // Apply sorting
      filteredContests.sort((a, b) => {
        switch (sortBy) {
          case 'newest':
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
          default:
            return 0;
        }
      });
      
      setDisplayedContests(filteredContests);
      
      // Group contests by status for display
      setOpenContests(filteredContests.filter(contest => contest.status === 'open'));
      setEvaluationContests(filteredContests.filter(contest => contest.status === 'evaluation'));
      setClosedContests(filteredContests.filter(contest => contest.status === 'closed'));
      
      // Estimate total count (backend doesn't return total count yet)
      setTotalCount(contests.length === itemsPerPage ? (currentPage * itemsPerPage) + 1 : skip + contests.length);
    } catch (error) {
      console.error("Error fetching contests:", error);
      setDisplayedContests([]);
      setOpenContests([]);
      setEvaluationContests([]);
      setClosedContests([]);
    }
    setIsLoading(false);
  };

  // Fetch contests whenever filters or pagination change
  useEffect(() => {
    fetchContests();
  }, [currentPage, searchTerm, statusFilter, selectedUser, isUserFilterActive]);

  // Apply client-side filtering when type filter or sort changes (since these aren't server-side yet)
  useEffect(() => {
    if (displayedContests.length > 0) {
      let result = [...displayedContests];
      
      // Apply type filter
      if (typeFilter !== 'all') {
        if (typeFilter === 'private') {
          result = result.filter(contest => contest.password_protected || !contest.publicly_listed);
        } else {
          result = result.filter(contest => !contest.password_protected && contest.publicly_listed);
        }
      }
      
      // Apply sorting
      result.sort((a, b) => {
        switch (sortBy) {
          case 'newest':
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
          default:
            return 0;
        }
      });
      
      // Group contests by status for display
      setOpenContests(result.filter(contest => contest.status === 'open'));
      setEvaluationContests(result.filter(contest => contest.status === 'evaluation'));
      setClosedContests(result.filter(contest => contest.status === 'closed'));
    }
  }, [typeFilter, sortBy, displayedContests]);

  // Update URL search params
  useEffect(() => {
    const params: Record<string, string> = {};
    if (statusFilter !== 'all') params.status = statusFilter;
    if (typeFilter !== 'all') params.type = typeFilter;
    if (sortBy !== 'newest') params.sort = sortBy;
    if (searchTerm) params.search = searchTerm;
    if (currentPage > 1) params.page = currentPage.toString();
    
    setSearchParams(params, { replace: true });
  }, [statusFilter, typeFilter, sortBy, searchTerm, currentPage, setSearchParams]);

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Handle user selection from search
  const handleUserSelect = (user: User | null) => {
    setSelectedUser(user);
    setIsUserFilterActive(!!user);
    setCurrentPage(1); // Reset to first page when filtering
  };

  // Handle filter changes with reset to page 1
  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
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
      
      {/* Filters and search */}
      <div className="bg-gray-50 p-4 rounded-lg mb-6">
        <div className="flex flex-col gap-4">
          {/* Search bars row */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-grow">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search Contests
              </label>
              <input
                type="text"
                placeholder="Search by title or description..."
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={searchTerm}
                onChange={(e) => handleSearchChange(e.target.value)}
              />
            </div>
            
            <div className="md:w-64">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Filter by Creator
              </label>
              <UserSearch
                onUserSelect={handleUserSelect}
                placeholder="Search creators..."
                selectedUser={selectedUser}
                className="w-full"
              />
            </div>
          </div>
          
          {/* Filter dropdowns row */}
          <div className="flex flex-col sm:flex-row gap-2">
            <select 
              className="px-3 py-2 border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={statusFilter}
              onChange={(e) => handleStatusFilterChange(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="open">Open</option>
              <option value="evaluation">In Evaluation</option>
              <option value="closed">Closed</option>
            </select>
            
            <select 
              className="px-3 py-2 border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={typeFilter}
              onChange={(e) => handleTypeFilterChange(e.target.value)}
            >
              <option value="all">All Types</option>
              <option value="public">Public</option>
              <option value="private">Private</option>
            </select>
            
            <select 
              className="px-3 py-2 border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={sortBy}
              onChange={(e) => handleSortChange(e.target.value)}
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="participants-high">Most Participants</option>
              <option value="participants-low">Fewest Participants</option>
              <option value="title-az">Title A-Z</option>
              <option value="title-za">Title Z-A</option>
            </select>
          </div>
          
          {/* Active filters display */}
          {isUserFilterActive && selectedUser && (
            <div className="text-sm text-gray-600">
              Filtering by creator: <span className="font-medium">{selectedUser.username}</span>
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