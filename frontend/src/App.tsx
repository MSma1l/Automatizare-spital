import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Auth pages
import LoginPage from './pages/auth/LoginPage';

// Admin pages
import AdminDashboard from './pages/admin/Dashboard';
import AdminDoctors from './pages/admin/Doctors';
import AdminPatients from './pages/admin/Patients';
import AdminResources from './pages/admin/Resources';
import AdminBeds from './pages/admin/Beds';
import AdminReports from './pages/admin/Reports';
import AdminAIAgents from './pages/admin/AIAgents';

// Doctor pages
import DoctorDashboard from './pages/doctor/Dashboard';
import DoctorAppointments from './pages/doctor/Appointments';
import DoctorPatients from './pages/doctor/Patients';
import DoctorChat from './pages/doctor/Chat';

// Patient pages
import PatientDashboard from './pages/patient/Dashboard';
import BookAppointment from './pages/patient/BookAppointment';
import PatientHistory from './pages/patient/History';
import PatientChat from './pages/patient/Chat';
import PatientAIAssistant from './pages/patient/AIAssistant';

// Shared
import Profile from './pages/Profile';

// Layout
import DashboardLayout from './components/Sidebar/DashboardLayout';

const ProtectedRoute: React.FC<{ children: React.ReactNode; roles?: string[] }> = ({
  children,
  roles,
}) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.includes(user.role)) return <Navigate to={`/${user.role}`} />;

  return <>{children}</>;
};

const AppRoutes: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-500">Se încarcă...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Public routes — single entry point for all roles */}
      <Route path="/login" element={user ? <Navigate to={`/${user.role}`} /> : <LoginPage />} />
      <Route path="/register" element={<Navigate to="/login" />} />

      {/* Admin routes */}
      <Route path="/admin" element={<ProtectedRoute roles={['admin']}><DashboardLayout /></ProtectedRoute>}>
        <Route index element={<AdminDashboard />} />
        <Route path="doctors" element={<AdminDoctors />} />
        <Route path="patients" element={<AdminPatients />} />
        <Route path="resources" element={<AdminResources />} />
        <Route path="beds" element={<AdminBeds />} />
        <Route path="reports" element={<AdminReports />} />
        <Route path="ai-agents" element={<AdminAIAgents />} />
        <Route path="profile" element={<Profile />} />
      </Route>

      {/* Doctor routes */}
      <Route path="/doctor" element={<ProtectedRoute roles={['doctor']}><DashboardLayout /></ProtectedRoute>}>
        <Route index element={<DoctorDashboard />} />
        <Route path="appointments" element={<DoctorAppointments />} />
        <Route path="patients" element={<DoctorPatients />} />
        <Route path="chat" element={<DoctorChat />} />
        <Route path="profile" element={<Profile />} />
      </Route>

      {/* Patient routes */}
      <Route path="/patient" element={<ProtectedRoute roles={['patient']}><DashboardLayout /></ProtectedRoute>}>
        <Route index element={<PatientDashboard />} />
        <Route path="book" element={<BookAppointment />} />
        <Route path="history" element={<PatientHistory />} />
        <Route path="chat" element={<PatientChat />} />
        <Route path="ai" element={<PatientAIAssistant />} />
        <Route path="profile" element={<Profile />} />
      </Route>

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/login" />} />
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="top-right" />
      </AuthProvider>
    </Router>
  );
};

export default App;
