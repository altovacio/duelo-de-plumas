import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import ProtectedRoute from './components/auth/ProtectedRoute';
import MainLayout from './components/Layout/MainLayout';

// Import actual page components
import LoginPage from './pages/Auth/LoginPage';
import RegisterPage from './pages/Auth/RegisterPage';
import HomePage from './pages/Home/HomePage';
import ContestListPage from './pages/ContestList/ContestListPage';
import ContestDetailPage from './pages/ContestDetail/ContestDetailPage';
import DashboardPage from './pages/Dashboard/DashboardPage';

// Placeholder components - these will be implemented later
const AdminDashboard = () => <div>Admin Dashboard</div>;

function App() {
  const loadUser = useAuthStore((state) => state.loadUser);
  const isLoading = useAuthStore((state) => state.isLoading);

  // Check for stored tokens and load user data on app startup
  useEffect(() => {
    loadUser();
  }, [loadUser]);

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <Router>
      <Routes>
        {/* Auth routes with layout */}
        <Route path="/login" element={<MainLayout><LoginPage /></MainLayout>} />
        <Route path="/register" element={<MainLayout><RegisterPage /></MainLayout>} />

        {/* Routes with MainLayout */}
        <Route path="/" element={<MainLayout><HomePage /></MainLayout>} />
        <Route path="/contests" element={<MainLayout><ContestListPage /></MainLayout>} />
        <Route path="/contests/:id" element={<MainLayout><ContestDetailPage /></MainLayout>} />

        {/* Protected routes - require authentication */}
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<MainLayout><DashboardPage /></MainLayout>} />
        </Route>

        {/* Admin routes - require admin role */}
        <Route element={<ProtectedRoute requireAdmin={true} />}>
          <Route path="/admin" element={<MainLayout><AdminDashboard /></MainLayout>} />
        </Route>

        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App; 