import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { Calendar, Users, MessageSquare, Clock, Sparkles, Activity } from 'lucide-react';

const DoctorDashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [todayAppts, setTodayAppts] = useState<any[]>([]);
  const [aiRecs, setAiRecs] = useState<any>(null);
  const [aiLoading, setAiLoading] = useState(true);
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

    api.get('/ai/recommendations')
      .then(res => setAiRecs(res.data))
      .catch(() => setAiRecs(null))
      .finally(() => setAiLoading(false));
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

      {/* AI Recommendations widget */}
      <div className="bg-gradient-to-br from-purple-50 to-primary-50 rounded-xl p-6 shadow-sm border border-purple-100 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 bg-gradient-to-br from-purple-500 to-primary-500 rounded-lg flex items-center justify-center">
              <Sparkles size={18} className="text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">Recomandări AI</h3>
              <p className="text-xs text-gray-500">Generate de RecommendationAgent (TF-IDF + RandomForest)</p>
            </div>
          </div>
          <span className="text-xs px-2 py-1 bg-white text-purple-700 rounded-full border border-purple-200">
            <Activity size={12} className="inline mr-1" /> Local AI
          </span>
        </div>

        {aiLoading ? (
          <p className="text-sm text-gray-400">Se încarcă recomandările...</p>
        ) : aiRecs && Array.isArray(aiRecs.recommendations) && aiRecs.recommendations.length > 0 ? (
          <div className="space-y-2">
            {aiRecs.recommendations.slice(0, 5).map((r: any, i: number) => (
              <div key={i} className="bg-white p-3 rounded-lg border border-purple-100">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <p className="text-sm text-gray-800">
                      {r.message || r.recommendation || r.action || JSON.stringify(r)}
                    </p>
                    {r.patient_name && (
                      <p className="text-xs text-gray-500 mt-1">Pacient: {r.patient_name}</p>
                    )}
                  </div>
                  {r.priority && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      r.priority === 'high' ? 'bg-red-100 text-red-700' :
                      r.priority === 'medium' ? 'bg-amber-100 text-amber-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {r.priority}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">
            Nu există recomandări noi. Agentul AI analizează pacienții cu programări recente și sugerează follow-up.
          </p>
        )}
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
