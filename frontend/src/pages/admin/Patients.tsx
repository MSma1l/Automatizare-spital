import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { UserCheck, UserX, Eye, X } from 'lucide-react';

const AdminPatients: React.FC = () => {
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPatient, setSelectedPatient] = useState<any>(null);

  const fetchPatients = () => {
    api.get('/admin/patients')
      .then(res => setPatients(res.data))
      .catch(() => toast.error('Eroare'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchPatients(); }, []);

  const viewPatient = async (id: number) => {
    try {
      const res = await api.get(`/admin/patients/${id}`);
      setSelectedPatient(res.data);
    } catch {
      toast.error('Eroare la încărcarea detaliilor');
    }
  };

  const toggleActive = async (id: number) => {
    try {
      const res = await api.put(`/admin/patients/${id}/toggle-active`);
      toast.success(res.data.message);
      fetchPatients();
    } catch {
      toast.error('Eroare');
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Gestionare Pacienți</h1>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Pacient</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Telefon</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Asigurare</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Acțiuni</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {patients.map(p => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <p className="font-medium text-gray-800">{p.first_name} {p.last_name}</p>
                  <p className="text-sm text-gray-400">{p.email}</p>
                </td>
                <td className="px-6 py-4 text-gray-600">{p.phone || '-'}</td>
                <td className="px-6 py-4 text-gray-600">{p.insurance_number || '-'}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${p.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {p.is_active ? 'Activ' : 'Inactiv'}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => viewPatient(p.id)} className="p-1.5 text-gray-400 hover:text-primary-500 rounded" title="Detalii">
                      <Eye size={16} />
                    </button>
                    <button onClick={() => toggleActive(p.id)} className={`p-1.5 rounded ${p.is_active ? 'text-gray-400 hover:text-red-500' : 'text-gray-400 hover:text-green-500'}`}>
                      {p.is_active ? <UserX size={16} /> : <UserCheck size={16} />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {patients.length === 0 && (
          <p className="text-center text-gray-400 py-8">Niciun pacient înregistrat</p>
        )}
      </div>

      {/* Detail modal */}
      {selectedPatient && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-lg max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-lg font-semibold">Detalii Pacient</h2>
              <button onClick={() => setSelectedPatient(null)} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <div className="p-6 space-y-3">
              <p><span className="text-gray-500">Nume:</span> <span className="font-medium">{selectedPatient.first_name} {selectedPatient.last_name}</span></p>
              <p><span className="text-gray-500">Email:</span> {selectedPatient.email}</p>
              <p><span className="text-gray-500">Telefon:</span> {selectedPatient.phone || '-'}</p>
              <p><span className="text-gray-500">Data nașterii:</span> {selectedPatient.birth_date || '-'}</p>
              <p><span className="text-gray-500">Adresă:</span> {selectedPatient.address || '-'}</p>
              <p><span className="text-gray-500">Nr. asigurare:</span> {selectedPatient.insurance_number || '-'}</p>

              {selectedPatient.appointments?.length > 0 && (
                <div className="mt-4">
                  <h3 className="font-medium text-gray-700 mb-2">Istoric consultații</h3>
                  <div className="space-y-2">
                    {selectedPatient.appointments.map((a: any) => (
                      <div key={a.id} className="p-3 bg-gray-50 rounded-lg text-sm">
                        <div className="flex justify-between">
                          <span className="font-medium">{a.doctor_name}</span>
                          <span className={`px-2 py-0.5 text-xs rounded-full ${
                            a.status === 'completed' ? 'bg-green-100 text-green-700' :
                            a.status === 'cancelled' ? 'bg-red-100 text-red-700' :
                            'bg-yellow-100 text-yellow-700'
                          }`}>{a.status}</span>
                        </div>
                        <p className="text-gray-500 mt-1">{new Date(a.date_time).toLocaleDateString('ro-RO')} - {a.type}</p>
                        {a.notes && <p className="text-gray-600 mt-1">{a.notes}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPatients;
