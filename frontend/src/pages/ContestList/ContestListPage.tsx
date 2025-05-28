import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getContests, Contest as ContestServiceType } from '../../services/contestService';
import ContestCard from '../../components/Contest/ContestCard';

const ContestListPage: React.FC = () => {
  const [allContests, setAllContests] = useState<ContestServiceType[]>([]);
  const [filteredContests, setFilteredContests] = useState<ContestServiceType[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get('status') || 'all');
  const [typeFilter, setTypeFilter] = useState<string>(searchParams.get('type') || 'all');
  const [sortBy, setSortBy] = useState<string>(searchParams.get('sort') || 'newest');
  const [searchTerm, setSearchTerm] = useState<string>(searchParams.get('search') || '');

  // Grouped contests
  const [openContests, setOpenContests] = useState<ContestServiceType[]>([]);
  const [evaluationContests, setEvaluationContests] = useState<ContestServiceType[]>([]);
  const [closedContests, setClosedContests] = useState<ContestServiceType[]>([]);

  useEffect(() => {
    const fetchContestsData = async () => {
      setIsLoading(true);
      try {
        const contestsData = await getContests({});
        setAllContests(contestsData);
      } catch (error) {
        console.error("Error fetching contests:", error);
        setAllContests([]);
      }
      setIsLoading(false);
    };
    
    fetchContestsData();
  }, []);

  // Apply filters and sorting whenever filter states or allContests change
  useEffect(() => {
    let result = [...allContests];
    
    // Apply status filter
    if (statusFilter !== 'all') {
      result = result.filter(contest => contest.status === statusFilter);
    }
    
    // Apply type filter
    if (typeFilter !== 'all') {
      if (typeFilter === 'private') {
        // Private contests are either password protected OR not publicly listed
        result = result.filter(contest => contest.password_protected || !contest.publicly_listed);
      } else {
        // Public contests are not password protected AND publicly listed
        result = result.filter(contest => !contest.password_protected && contest.publicly_listed);
      }
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
    
    setFilteredContests(result);
    
    // Group contests by status
    setOpenContests(result.filter(contest => contest.status === 'open'));
    setEvaluationContests(result.filter(contest => contest.status === 'evaluation'));
    setClosedContests(result.filter(contest => contest.status === 'closed'));
    
    // Update URL search params
    const params: Record<string, string> = {};
    if (statusFilter !== 'all') params.status = statusFilter;
    if (typeFilter !== 'all') params.type = typeFilter;
    if (sortBy !== 'newest') params.sort = sortBy;
    if (searchTerm) params.search = searchTerm;
    
    setSearchParams(params, { replace: true });
  }, [allContests, statusFilter, typeFilter, sortBy, searchTerm, setSearchParams]);

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
    </div>
  );
};

export default ContestListPage; 