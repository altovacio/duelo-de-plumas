import React from 'react';
import { Link } from 'react-router-dom';

const AdminDashboardPage: React.FC = () => {
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
            <p className="text-2xl font-bold">Loading...</p>
          </div>
          
          <div className="bg-green-50 rounded-lg p-4">
            <h3 className="font-medium text-green-800 mb-1">Active Contests</h3>
            <p className="text-2xl font-bold">Loading...</p>
          </div>
          
          <div className="bg-purple-50 rounded-lg p-4">
            <h3 className="font-medium text-purple-800 mb-1">Total Credits Assigned</h3>
            <p className="text-2xl font-bold">Loading...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardPage; 