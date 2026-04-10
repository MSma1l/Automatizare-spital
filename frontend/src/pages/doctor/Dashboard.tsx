import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { Calendar, Users, MessageSquare, Clock } from 'lucide-react';

const DoctorDashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [todayAppts, setTodayAppts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/doctor/stats'),
      api.get('/doctor/appointments?status_filter=confirmed'),
    ]).then(([s, a]) => {
      setStats(s.data);
      const today = new Date().toISOString().split('T')[0];
      setTodayAppts(a.data.filter((ap: any) => ap.date_time.startsWith(today)));
    }).catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  const cards = stats ? [
    { label: 'Programări Azi', value: stats.appointments_today, icon: <Calendar size={24} />, color: 'bg-blue-500' },
    { label: 'Pacienți Totali', value: stats.total_patients, icon: <Users size={24} />, color: 'bg-green-500' },
    { label: 'Mesaje Necitite', value: stats.unread_messages, icon: <MessageSquare size={24} />, color: 'bg-purple-500' },
    { label: 'În Așteptare', value: stats.pending_appointments, icon: <Clock size={24} />, color: 'bg-orange-500' },
  ] : [];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Dashboard Medic</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {cards.map(card => (
          <div key={card.label} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-500">{card.label}</p>
                <p className="text-3xl font-bold text-gray-800 mt-1">{card.value}</p>
              </div>
              <div className={`${card.color} p-3 rounded-lg text-white`}>{card.icon}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Today's appointments */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-700 mb-4">Programările de Azi</h3>
        {todayAppts.length > 0 ? (
          <div className="space-y-3">
            {todayAppts.map(a => (
              <div key={a.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-primary-600 font-medium text-sm">
                      {a.patient_name.split(' ').map((n: string) => n[0]).join('')}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">{a.patient_name}</p>
                    <p className="text-sm text-gray-500">{a.type === 'video' ? 'Video consultație' : 'Consultație'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium text-gray-800">{new Date(a.date_time).toLocaleTimeString('ro-RO', { hour: '2-digit', minute: '2-digit' })}</p>
                  <p className="text-sm text-gray-500">{a.duration_minutes} min</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-4">Nu aveți programări pentru azi</p>
        )}
      </div>
    </div>
  );
};

export default DoctorDashboard;
