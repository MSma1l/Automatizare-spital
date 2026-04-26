import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import {
  LayoutDashboard, Users, Calendar, MessageSquare, BedDouble,
  Package, FileBarChart, UserCircle, LogOut, Bell, Menu, X,
  Stethoscope, ClipboardList, History, Search, Sparkles,
} from 'lucide-react';

const navConfig: Record<string, Array<{ to: string; icon: React.ReactNode; label: string }>> = {
  admin: [
    { to: '/admin', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { to: '/admin/doctors', icon: <Stethoscope size={20} />, label: 'Medici' },
    { to: '/admin/patients', icon: <Users size={20} />, label: 'Pacienți' },
    { to: '/admin/resources', icon: <Package size={20} />, label: 'Resurse' },
    { to: '/admin/beds', icon: <BedDouble size={20} />, label: 'Paturi' },
    { to: '/admin/reports', icon: <FileBarChart size={20} />, label: 'Rapoarte' },
    { to: '/admin/ai-agents', icon: <Sparkles size={20} />, label: 'Agenți AI' },
  ],
  doctor: [
    { to: '/doctor', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { to: '/doctor/appointments', icon: <Calendar size={20} />, label: 'Programări' },
    { to: '/doctor/patients', icon: <Users size={20} />, label: 'Pacienți' },
    { to: '/doctor/chat', icon: <MessageSquare size={20} />, label: 'Mesaje' },
  ],
  patient: [
    { to: '/patient', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { to: '/patient/book', icon: <Search size={20} />, label: 'Programare' },
    { to: '/patient/history', icon: <History size={20} />, label: 'Istoric' },
    { to: '/patient/chat', icon: <MessageSquare size={20} />, label: 'Mesaje' },
    { to: '/patient/ai', icon: <Sparkles size={20} />, label: 'Asistent AI' },
  ],
};

const DashboardLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [showNotif, setShowNotif] = useState(false);

  const role = user?.role || 'patient';
  const links = navConfig[role] || [];
  const displayName = user?.profile
    ? `${user.profile.first_name} ${user.profile.last_name}`
    : user?.email || '';

  useEffect(() => {
    let active = true;
    const fetchNotifs = () => {
      api.get('/notifications?unread_only=true')
        .then(res => { if (active) setNotifications(res.data); })
        .catch(() => {});
    };
    fetchNotifs();
    const id = window.setInterval(fetchNotifs, 30000);
    return () => { active = false; window.clearInterval(id); };
  }, []);

  const markRead = async (id: number) => {
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch {
      /* noop */
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const unreadCount = notifications.length;

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-200 ease-in-out
        lg:relative lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
              <Stethoscope size={18} className="text-white" />
            </div>
            <span className="font-bold text-gray-800">Hospital DSS</span>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-gray-500">
            <X size={20} />
          </button>
        </div>

        <nav className="mt-6 px-3">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === `/${role}`}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              {link.icon}
              <span>{link.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100">
          <button
            onClick={() => { navigate(`/${role}/profile`); setSidebarOpen(false); }}
            className="flex items-center gap-3 px-3 py-2 w-full rounded-lg hover:bg-gray-50 transition-colors text-left"
            title="Profil personal"
          >
            {user?.profile?.photo_url ? (
              <img
                src={user.profile.photo_url}
                alt="avatar"
                className="w-10 h-10 rounded-full object-cover"
              />
            ) : (
              <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                <UserCircle size={24} className="text-primary-600" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-700 truncate">{displayName}</p>
              <p className="text-xs text-gray-400 capitalize">{role}</p>
            </div>
          </button>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-4 py-2 mt-2 text-sm text-red-600 rounded-lg hover:bg-red-50 transition-colors"
          >
            <LogOut size={18} />
            Deconectare
          </button>
        </div>
      </aside>

      {/* Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-6">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-gray-600">
            <Menu size={24} />
          </button>

          <div className="flex-1" />

          <div className="flex items-center gap-4">
            {/* Notifications */}
            <div className="relative">
              <button
                onClick={() => setShowNotif(!showNotif)}
                className="relative p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
              >
                <Bell size={20} />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {showNotif && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-96 overflow-y-auto">
                  <div className="p-3 border-b border-gray-100 flex justify-between items-center">
                    <span className="font-medium text-gray-700">Notificări</span>
                    {unreadCount > 0 && (
                      <button
                        onClick={() => {
                          api.put('/notifications/read-all').then(() => setNotifications([]));
                        }}
                        className="text-xs text-primary-500 hover:text-primary-600"
                      >
                        Marchează toate citite
                      </button>
                    )}
                  </div>
                  {notifications.length === 0 ? (
                    <p className="p-4 text-center text-gray-400 text-sm">Nicio notificare nouă</p>
                  ) : (
                    notifications.map((n) => {
                      const accent =
                        n.type === 'urgent' ? 'border-l-red-500' :
                        n.type === 'warning' ? 'border-l-orange-400' :
                        n.type === 'appointment' ? 'border-l-blue-500' :
                        n.type === 'message' ? 'border-l-emerald-500' :
                        'border-l-primary-400';
                      return (
                        <div
                          key={n.id}
                          onClick={() => markRead(n.id)}
                          className={`p-3 border-b border-gray-50 hover:bg-gray-50 cursor-pointer border-l-4 ${accent}`}
                        >
                          <p className="text-sm font-medium text-gray-700">{n.title}</p>
                          <p className="text-xs text-gray-500 mt-1">{n.message}</p>
                          <p className="text-[10px] text-gray-400 mt-1">
                            {new Date(n.created_at).toLocaleString('ro-RO')}
                          </p>
                        </div>
                      );
                    })
                  )}
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
