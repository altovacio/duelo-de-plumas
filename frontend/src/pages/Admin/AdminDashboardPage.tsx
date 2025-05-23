import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getAdminUsers } from '../../services/userService';
import { getContests } from '../../services/contestService';
import { toast } from 'react-hot-toast';

interface AdminStats {
  totalUsers: number | null;
  activeContests: number | null;
  totalCreditsAssigned: number | null;
}

const AdminDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<AdminStats>({ 
    totalUsers: null, 
    activeContests: null, 
    totalCreditsAssigned: null 
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      setIsLoading(true);
      try {
        const usersData = await getAdminUsers();
        const totalUsers = usersData.length;
        const totalCreditsAssigned = usersData.reduce((sum, user) => sum + (user.credits || 0), 0);

        const openContests = await getContests({ status: 'open' });
        const evaluationContests = await getContests({ status: 'evaluation' });
        const activeContests = openContests.length + evaluationContests.length;

        setStats({
          totalUsers,
          activeContests,
          totalCreditsAssigned
        });
      } catch (error) {
        console.error("Error fetching admin dashboard stats:", error);
        toast.error("Failed to load platform statistics. Please try again later.");
        setStats({ totalUsers: 0, activeContests: 0, totalCreditsAssigned: 0 }); // Show 0 on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <Link to="/admin/users" className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
          <h2 className="text-xl font-semibold mb-2">User Management</h2>
          <p className="text-gray-600">Manage users and assign credits</p>
        </Link>
        
        <Link to="/admin/agents" className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
          <h2 className="text-xl font-semibold mb-2">AI Agents</h2>
          <p className="text-gray-600">Manage global AI agents</p>
        </Link>
        
        <Link to="/admin/monitoring" className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
          <h2 className="text-xl font-semibold mb-2">Credit Monitoring</h2>
          <p className="text-gray-600">Monitor credit usage and costs</p>
        </Link>
        
        <Link to="/admin/contests" className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
          <h2 className="text-xl font-semibold mb-2">Contests</h2>
          <p className="text-gray-600">Oversee all contests</p>
        </Link>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Platform Overview</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="font-medium text-blue-800 mb-1">Total Users</h3>
            <p className="text-2xl font-bold">
              {isLoading ? 'Loading...' : stats.totalUsers !== null ? stats.totalUsers : 'Error'}
            </p>
          </div>
          
          <div className="bg-green-50 rounded-lg p-4">
            <h3 className="font-medium text-green-800 mb-1">Active Contests</h3>
            <p className="text-2xl font-bold">
              {isLoading ? 'Loading...' : stats.activeContests !== null ? stats.activeContests : 'Error'}
            </p>
          </div>
          
          <div className="bg-purple-50 rounded-lg p-4">
            <h3 className="font-medium text-purple-800 mb-1">Total Credits Assigned</h3>
            <p className="text-2xl font-bold">
              {isLoading ? 'Loading...' : stats.totalCreditsAssigned !== null ? stats.totalCreditsAssigned.toLocaleString() : 'Error'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardPage; 