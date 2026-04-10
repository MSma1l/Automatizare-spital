import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { FileText, Calendar } from 'lucide-react';

const PatientHistory: React.FC = () => {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/patient/appointments'),
      api.get('/patient/history'),
    ]).then(([appts, hist]) => {
      setAppointments(appts.data);
      setHistory(hist.data);
    }).catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const cancelAppointment = async (id: number) => {
    try {
      await api.put(`/patient/appointments/${id}/cancel`);
      setAppointments(prev => prev.map(a => a.id === id ? { ...a, status: 'cancelled' } : a));
    } catch {
      // handle error
    }
  };

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    confirmed: 'bg-green-100 text-green-700',
    completed: 'bg-blue-100 text-blue-700',
    rejected: 'bg-red-100 text-red-700',
    cancelled: 'bg-gray-100 text-gray-700',
  };

  const statusLabels: Record<string, string> = {
    pending: 'În așteptare', confirmed: 'Confirmată', completed: 'Finalizată', rejected: 'Refuzată', cancelled: 'Anulată',
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  const upcoming = appointments.filter(a => ['pending', 'confirmed'].includes(a.status));
  const past = appointments.filter(a => ['completed', 'cancelled', 'rejected'].includes(a.status));

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Istoric & Programări</h1>

      {/* Upcoming */}
      {upcoming.length > 0 && (
        <div className="mb-8">
          <h2 className="font-semibold text-gray-700 mb-3 flex items-center gap-2"><Calendar size={18} /> Programări Active</h2>
          <div className="space-y-3">
            {upcoming.map(a => (
              <div key={a.id} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-800">{a.doctor_name}</p>
                    <p className="text-sm text-gray-500">{a.doctor_specialty}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      {new Date(a.date_time).toLocaleDateString('ro-RO', { weekday: 'long', day: 'numeric', month: 'long' })} la{' '}
                      {new Date(a.date_time).toLocaleTimeString('ro-RO', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 text-xs rounded-full ${statusColors[a.status]}`}>{statusLabels[a.status]}</span>
                    {['pending', 'confirmed'].includes(a.status) && (
                      <button onClick={() => cancelAppointment(a.id)}
                        className="px-3 py-1 text-xs text-red-500 border border-red-200 rounded-full hover:bg-red-50">
                        Anulează
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* History */}
      <h2 className="font-semibold text-gray-700 mb-3 flex items-center gap-2"><FileText size={18} /> Istoric Consultații</h2>
      {history.length > 0 ? (
        <div className="space-y-3">
          {history.map(h => (
            <div key={h.id} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-medium text-gray-800">{h.doctor_name}</p>
                  <p className="text-sm text-gray-500">{h.doctor_specialty}</p>
                </div>
                <p className="text-sm text-gray-400">{new Date(h.date_time).toLocaleDateString('ro-RO')}</p>
              </div>
              {h.notes && (
                <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-600 mt-2">
                  <span className="font-medium">Note medic:</span> {h.notes}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-center text-gray-400 py-8">Nu aveți consultații finalizate</p>
      )}
    </div>
  );
};

export default PatientHistory;
