import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

// Contest interface (same as in HomePage for consistency)
interface Contest {
  id: number;
  title: string;
  description: string;
  participantCount: number;
  lastModified: string;
  endDate?: string;
  type: 'public' | 'private';
  status: 'open' | 'evaluation' | 'closed';
}

const ContestListPage: React.FC = () => {
  const [contests, setContests] = useState<Contest[]>([]);
  const [filteredContests, setFilteredContests] = useState<Contest[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get('status') || 'all');
  const [typeFilter, setTypeFilter] = useState<string>(searchParams.get('type') || 'all');
  const [sortBy, setSortBy] = useState<string>(searchParams.get('sort') || 'newest');
  const [searchTerm, setSearchTerm] = useState<string>(searchParams.get('search') || '');

  useEffect(() => {
    // This would be replaced with an actual API call
    const fetchContests = () => {
      setIsLoading(true);
      
      // Simulate API delay
      setTimeout(() => {
        // Sample data - would come from backend in a real app
        const allContests: Contest[] = [
          {
            id: 1,
            title: "Summer Poetry Challenge",
            description: "Share your best summer-inspired poems.",
            participantCount: 12,
            lastModified: "2023-06-15",
            endDate: "2023-07-30",
            type: "public",
            status: "open"
          },
          {
            id: 2,
            title: "Short Story Festival",
            description: "Submit your short stories under 5000 words.",
            participantCount: 24,
            lastModified: "2023-06-10",
            type: "public",
            status: "open"
          },
          {
            id: 3,
            title: "Spring Fiction Competition",
            description: "Fiction stories inspired by spring themes.",
            participantCount: 35,
            lastModified: "2023-05-25",
            endDate: "2023-06-01",
            type: "public",
            status: "closed"
          },
          {
            id: 4,
            title: "Microfiction Challenge",
            description: "Tell your story in less than 100 words.",
            participantCount: 48,
            lastModified: "2023-05-15",
            endDate: "2023-05-30",
            type: "public",
            status: "closed"
          },
          {
            id: 5,
            title: "Private Writing Workshop",
            description: "A private workshop for advanced writers.",
            participantCount: 8,
            lastModified: "2023-06-05",
            type: "private",
            status: "open"
          },
          {
            id: 6,
            title: "Sci-Fi Short Stories",
            description: "Write your best sci-fi short story.",
            participantCount: 15,
            lastModified: "2023-05-20",
            type: "public",
            status: "evaluation"
          }
        ];
        
        setContests(allContests);
        setIsLoading(false);
      }, 1000);
    };
    
    fetchContests();
  }, []);

  // Apply filters and sorting whenever filter states change
  useEffect(() => {
    let result = [...contests];
    
    // Apply status filter
    if (statusFilter !== 'all') {
      result = result.filter(contest => contest.status === statusFilter);
    }
    
    // Apply type filter
    if (typeFilter !== 'all') {
      result = result.filter(contest => contest.type === typeFilter);
    }
    
    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      result = result.filter(contest => 
        contest.title.toLowerCase().includes(search) || 
        contest.description.toLowerCase().includes(search)
      );
    }
    
    // Apply sorting
    result.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.lastModified).getTime() - new Date(a.lastModified).getTime();
        case 'oldest':
          return new Date(a.lastModified).getTime() - new Date(b.lastModified).getTime();
        case 'participants-high':
          return b.participantCount - a.participantCount;
        case 'participants-low':
          return a.participantCount - b.participantCount;
        case 'title-az':
          return a.title.localeCompare(b.title);
        case 'title-za':
          return b.title.localeCompare(a.title);
        default:
          return 0;
      }
    });
    
    setFilteredContests(result);
    
    // Update URL search params
    const params: Record<string, string> = {};
    if (statusFilter !== 'all') params.status = statusFilter;
    if (typeFilter !== 'all') params.type = typeFilter;
    if (sortBy !== 'newest') params.sort = sortBy;
    if (searchTerm) params.search = searchTerm;
    
    setSearchParams(params, { replace: true });
  }, [contests, statusFilter, typeFilter, sortBy, searchTerm, setSearchParams]);

  const ContestCard = ({ contest }: { contest: Contest }) => (
    <div className="border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow bg-white">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-semibold">{contest.title}</h3>
        <div className="flex space-x-2">
          <div 
            className={`text-xs px-2 py-1 rounded-full ${
              contest.type === 'public' 
                ? 'bg-blue-100 text-blue-800' 
                : 'bg-purple-100 text-purple-800'
            }`}
          >
            {contest.type.charAt(0).toUpperCase() + contest.type.slice(1)}
          </div>
          <div 
            className={`text-xs px-2 py-1 rounded-full ${
              contest.status === 'open' 
                ? 'bg-green-100 text-green-800' 
                : contest.status === 'evaluation' 
                  ? 'bg-yellow-100 text-yellow-800' 
                  : 'bg-gray-100 text-gray-800'
            }`}
          >
            {contest.status.charAt(0).toUpperCase() + contest.status.slice(1)}
          </div>
        </div>
      </div>
      <p className="text-sm text-gray-600 mb-3">{contest.description}</p>
      <div className="flex justify-between text-xs text-gray-500">
        <span>{contest.participantCount} participants</span>
        <span>Last updated: {new Date(contest.lastModified).toLocaleDateString()}</span>
      </div>
      <div className="mt-3">
        <Link 
          to={`/contests/${contest.id}`} 
          className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
        >
          View details →
        </Link>
      </div>
    </div>
  );

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Literary Contests</h1>
        <p className="text-gray-600">Browse all available contests and find one to participate in.</p>
      </div>
      
      {/* Filters and search */}
      <div className="bg-gray-50 p-4 rounded-lg mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex-grow">
            <input
              type="text"
              placeholder="Search contests..."
              className="w-full px-3 py-2 border rounded-lg"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="flex flex-col sm:flex-row gap-2">
            <select 
              className="px-3 py-2 border rounded-lg bg-white"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="open">Open</option>
              <option value="evaluation">In Evaluation</option>
              <option value="closed">Closed</option>
            </select>
            
            <select 
              className="px-3 py-2 border rounded-lg bg-white"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="all">All Types</option>
              <option value="public">Public</option>
              <option value="private">Private</option>
            </select>
            
            <select 
              className="px-3 py-2 border rounded-lg bg-white"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="participants-high">Most Participants</option>
              <option value="participants-low">Fewest Participants</option>
              <option value="title-az">Title A-Z</option>
              <option value="title-za">Title Z-A</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Contest listing */}
      {isLoading ? (
        <div className="text-center py-16">
          <p className="text-gray-500">Loading contests...</p>
        </div>
      ) : filteredContests.length === 0 ? (
        <div className="text-center py-16 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No contests found matching your criteria.</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {filteredContests.map(contest => (
            <ContestCard key={contest.id} contest={contest} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ContestListPage; 