import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { Check, X, FileText, Filter } from 'lucide-react';

const DoctorAppointments: React.FC = () => {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [notesModal, setNotesModal] = useState<{ id: number; notes: string } | null>(null);

  const fetchAppointments = () => {
    const params = statusFilter ? `?status_filter=${statusFilter}` : '';
    api.get(`/doctor/appointments${params}`)
      .then(res => setAppointments(res.data))
      .catch(() => toast.error('Eroare'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchAppointments(); }, [statusFilter]);

  const updateStatus = async (id: number, status: string) => {
    try {
      await api.put(`/doctor/appointments/${id}`, { status });
      toast.success(`Programare ${status === 'confirmed' ? 'confirmată' : status === 'rejected' ? 'refuzată' : 'actualizată'}`);
      fetchAppointments();
    } catch {
      toast.error('Eroare');
    }
  };

  const saveNotes = async () => {
    if (!notesModal) return;
    try {
      await api.put(`/doctor/appointments/${notesModal.id}`, { notes: notesModal.notes });
      toast.success('Note salvate');
      setNotesModal(null);
      fetchAppointments();
    } catch {
      toast.error('Eroare');
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

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Programări</h1>
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-gray-400" />
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none">
            <option value="">Toate</option>
            <option value="pending">În așteptare</option>
            <option value="confirmed">Confirmate</option>
            <option value="completed">Finalizate</option>
          </select>
        </div>
      </div>

      <div className="space-y-3">
        {appointments.map(a => (
          <div key={a.id} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-primary-600 font-medium">
                    {a.patient_name.split(' ').map((n: string) => n[0]).join('')}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-800">{a.patient_name}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(a.date_time).toLocaleDateString('ro-RO')} la{' '}
                    {new Date(a.date_time).toLocaleTimeString('ro-RO', { hour: '2-digit', minute: '2-digit' })}
                    {' '}({a.duration_minutes} min)
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-3 py-1 text-xs rounded-full ${statusColors[a.status] || 'bg-gray-100'}`}>
                  {statusLabels[a.status] || a.status}
                </span>
                {a.status === 'pending' && (
                  <>
                    <button onClick={() => updateStatus(a.id, 'confirmed')}
                      className="p-2 text-green-500 hover:bg-green-50 rounded-lg" title="Confirmă">
                      <Check size={18} />
                    </button>
                    <button onClick={() => updateStatus(a.id, 'rejected')}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg" title="Refuză">
                      <X size={18} />
                    </button>
                  </>
                )}
                {a.status === 'confirmed' && (
                  <button onClick={() => updateStatus(a.id, 'completed')}
                    className="px-3 py-1 text-xs bg-blue-500 text-white rounded-full hover:bg-blue-600">
                    Finalizează
                  </button>
                )}
                <button onClick={() => setNotesModal({ id: a.id, notes: a.notes || '' })}
                  className="p-2 text-gray-400 hover:text-primary-500 rounded-lg" title="Note">
                  <FileText size={18} />
                </button>
              </div>
            </div>
            {a.notes && (
              <div className="mt-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
                <span className="font-medium">Note:</span> {a.notes}
              </div>
            )}
          </div>
        ))}
        {appointments.length === 0 && <p className="text-center text-gray-400 py-8">Nicio programare</p>}
      </div>

      {/* Notes modal */}
      {notesModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-lg font-semibold">Note Consultație</h2>
              <button onClick={() => setNotesModal(null)} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <div className="p-6">
              <textarea
                value={notesModal.notes}
                onChange={e => setNotesModal({ ...notesModal, notes: e.target.value })}
                rows={5}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
                placeholder="Adăugați note despre consultație..."
              />
              <div className="flex justify-end gap-3 mt-4">
                <button onClick={() => setNotesModal(null)} className="px-4 py-2 text-gray-600 border rounded-lg hover:bg-gray-50">Anulează</button>
                <button onClick={saveNotes} className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600">Salvează</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DoctorAppointments;
