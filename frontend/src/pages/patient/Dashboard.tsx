import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { Calendar, MessageSquare, ClipboardList, Search } from 'lucide-react';

const PatientDashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/patient/stats')
      .then(res => setStats(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Dashboard Pacient</h1>

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <button onClick={() => navigate('/patient/book')}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:border-primary-200 hover:shadow-md transition text-left">
          <div className="bg-primary-100 p-3 rounded-lg w-fit mb-3"><Search size={24} className="text-primary-600" /></div>
          <p className="font-medium text-gray-800">Programează Consultație</p>
          <p className="text-sm text-gray-500 mt-1">Caută un medic și rezervă</p>
        </button>
        <button onClick={() => navigate('/patient/chat')}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:border-primary-200 hover:shadow-md transition text-left">
          <div className="bg-purple-100 p-3 rounded-lg w-fit mb-3"><MessageSquare size={24} className="text-purple-600" /></div>
          <p className="font-medium text-gray-800">Mesaje</p>
          <p className="text-sm text-gray-500 mt-1">{stats?.unread_messages || 0} necitite</p>
        </button>
        <button onClick={() => navigate('/patient/history')}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:border-primary-200 hover:shadow-md transition text-left">
          <div className="bg-green-100 p-3 rounded-lg w-fit mb-3"><ClipboardList size={24} className="text-green-600" /></div>
          <p className="font-medium text-gray-800">Istoric Medical</p>
          <p className="text-sm text-gray-500 mt-1">{stats?.total_appointments || 0} consultații</p>
        </button>
      </div>

      {/* Next appointment */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-700 mb-4">Următoarea Programare</h3>
        {stats?.next_appointment ? (
          <div className="flex items-center gap-4 p-4 bg-primary-50 rounded-lg">
            <div className="bg-primary-500 p-3 rounded-lg text-white"><Calendar size={24} /></div>
            <div>
              <p className="font-medium text-gray-800">{stats.next_appointment.doctor_name}</p>
              <p className="text-sm text-gray-600">
                {new Date(stats.next_appointment.date_time).toLocaleDateString('ro-RO', {
                  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
                })} la {new Date(stats.next_appointment.date_time).toLocaleTimeString('ro-RO', { hour: '2-digit', minute: '2-digit' })}
              </p>
              <span className={`inline-block mt-1 px-2 py-0.5 text-xs rounded-full ${
                stats.next_appointment.status === 'confirmed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              }`}>
                {stats.next_appointment.status === 'confirmed' ? 'Confirmată' : 'În așteptare'}
              </span>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-gray-400">Nu aveți nicio programare viitoare</p>
            <button onClick={() => navigate('/patient/book')}
              className="mt-2 text-primary-500 hover:text-primary-600 text-sm font-medium">
              Programați acum →
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientDashboard;
