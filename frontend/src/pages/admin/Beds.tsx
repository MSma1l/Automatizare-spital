import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { Plus, Edit2, X, BedDouble } from 'lucide-react';

const WARDS = ['Secția ATI', 'Secția Chirurgie', 'Secția Medicină Internă', 'Secția Cardiologie', 'Secția Pediatrie', 'Secția Neurologie', 'Secția Ortopedie'];

const AdminBeds: React.FC = () => {
  const [beds, setBeds] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [filterWard, setFilterWard] = useState('');
  const [form, setForm] = useState({ room_number: '', ward: '', status: 'free', patient_id: null as number | null });

  const fetchBeds = () => {
    const params = filterWard ? `?ward=${filterWard}` : '';
    api.get(`/admin/beds${params}`)
      .then(res => setBeds(res.data))
      .catch(() => toast.error('Eroare'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchBeds(); }, [filterWard]);

  const openCreate = () => {
    setEditId(null);
    setForm({ room_number: '', ward: WARDS[0], status: 'free', patient_id: null });
    setShowModal(true);
  };

  const openEdit = (b: any) => {
    setEditId(b.id);
    setForm({ room_number: b.room_number, ward: b.ward, status: b.status, patient_id: b.patient_id });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editId) {
        await api.put(`/admin/beds/${editId}`, form);
        toast.success('Pat actualizat');
      } else {
        await api.post('/admin/beds', form);
        toast.success('Pat creat');
      }
      setShowModal(false);
      fetchBeds();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Eroare');
    }
  };

  const statusColors: Record<string, string> = {
    free: 'bg-green-100 text-green-700 border-green-200',
    occupied: 'bg-red-100 text-red-700 border-red-200',
    maintenance: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    reserved: 'bg-blue-100 text-blue-700 border-blue-200',
  };

  const statusLabels: Record<string, string> = {
    free: 'Liber', occupied: 'Ocupat', maintenance: 'Mentenanță', reserved: 'Rezervat',
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Gestionare Paturi</h1>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600">
          <Plus size={18} /> Adaugă Pat
        </button>
      </div>

      <div className="mb-4">
        <select value={filterWard} onChange={e => setFilterWard(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none">
          <option value="">Toate secțiile</option>
          {WARDS.map(w => <option key={w} value={w}>{w}</option>)}
        </select>
      </div>

      {/* Grid view */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {beds.map(b => (
          <div
            key={b.id}
            onClick={() => openEdit(b)}
            className={`p-4 rounded-xl border-2 cursor-pointer transition hover:shadow-md ${statusColors[b.status] || 'bg-gray-100 text-gray-700 border-gray-200'}`}
          >
            <div className="flex items-center justify-between mb-2">
              <BedDouble size={20} />
              <span className="text-xs font-medium">{statusLabels[b.status]}</span>
            </div>
            <p className="font-bold text-lg">#{b.room_number}</p>
            <p className="text-xs mt-1 opacity-75">{b.ward}</p>
            {b.patient_name && <p className="text-xs mt-1 font-medium">{b.patient_name}</p>}
          </div>
        ))}
      </div>
      {beds.length === 0 && <p className="text-center text-gray-400 py-8">Niciun pat adăugat</p>}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-lg font-semibold">{editId ? 'Editare Pat' : 'Adaugă Pat'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Număr cameră *</label>
                <input type="text" required value={form.room_number} onChange={e => setForm({...form, room_number: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Secție *</label>
                <select value={form.ward} onChange={e => setForm({...form, ward: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none">
                  {WARDS.map(w => <option key={w} value={w}>{w}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select value={form.status} onChange={e => setForm({...form, status: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none">
                  <option value="free">Liber</option>
                  <option value="occupied">Ocupat</option>
                  <option value="maintenance">Mentenanță</option>
                  <option value="reserved">Rezervat</option>
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-gray-600 border rounded-lg hover:bg-gray-50">Anulează</button>
                <button type="submit" className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600">{editId ? 'Salvează' : 'Creează'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminBeds;
