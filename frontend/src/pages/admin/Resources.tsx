import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { Plus, Edit2, Trash2, X, AlertTriangle } from 'lucide-react';

const TYPES = [
  { value: 'equipment', label: 'Echipament' },
  { value: 'medication', label: 'Medicament' },
  { value: 'room', label: 'Sală' },
  { value: 'supply', label: 'Consumabil' },
];

const AdminResources: React.FC = () => {
  const [resources, setResources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [filterType, setFilterType] = useState('');
  const [form, setForm] = useState({
    name: '', type: 'equipment', quantity: 0, min_quantity: 0,
    location: '', status: 'available', description: '',
  });

  const fetchResources = () => {
    const params = filterType ? `?resource_type=${filterType}` : '';
    api.get(`/admin/resources${params}`)
      .then(res => setResources(res.data))
      .catch(() => toast.error('Eroare'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchResources(); }, [filterType]);

  const openCreate = () => {
    setEditId(null);
    setForm({ name: '', type: 'equipment', quantity: 0, min_quantity: 0, location: '', status: 'available', description: '' });
    setShowModal(true);
  };

  const openEdit = (r: any) => {
    setEditId(r.id);
    setForm({ name: r.name, type: r.type, quantity: r.quantity, min_quantity: r.min_quantity, location: r.location || '', status: r.status, description: r.description || '' });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editId) {
        await api.put(`/admin/resources/${editId}`, form);
        toast.success('Resursă actualizată');
      } else {
        await api.post('/admin/resources', form);
        toast.success('Resursă creată');
      }
      setShowModal(false);
      fetchResources();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Eroare');
    }
  };

  const deleteResource = async (id: number) => {
    if (!window.confirm('Sigur doriți ștergerea?')) return;
    try {
      await api.delete(`/admin/resources/${id}`);
      toast.success('Resursă ștearsă');
      fetchResources();
    } catch {
      toast.error('Eroare');
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Gestionare Resurse</h1>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600">
          <Plus size={18} /> Adaugă Resursă
        </button>
      </div>

      {/* Filter */}
      <div className="mb-4">
        <select value={filterType} onChange={e => setFilterType(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none">
          <option value="">Toate tipurile</option>
          {TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Resursă</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Tip</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Cantitate</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Locație</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Acțiuni</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {resources.map(r => (
              <tr key={r.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    {r.quantity <= r.min_quantity && r.min_quantity > 0 && (
                      <AlertTriangle size={16} className="text-red-500" />
                    )}
                    <span className="font-medium text-gray-800">{r.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-600">{TYPES.find(t => t.value === r.type)?.label || r.type}</td>
                <td className="px-6 py-4">
                  <span className={r.quantity <= r.min_quantity && r.min_quantity > 0 ? 'text-red-600 font-medium' : 'text-gray-600'}>
                    {r.quantity}
                  </span>
                  {r.min_quantity > 0 && <span className="text-gray-400 text-sm"> / min: {r.min_quantity}</span>}
                </td>
                <td className="px-6 py-4 text-gray-600">{r.location || '-'}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    r.status === 'available' ? 'bg-green-100 text-green-700' :
                    r.status === 'in_use' ? 'bg-blue-100 text-blue-700' :
                    r.status === 'maintenance' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {r.status === 'available' ? 'Disponibil' : r.status === 'in_use' ? 'În uz' : r.status === 'maintenance' ? 'Mentenanță' : 'Epuizat'}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => openEdit(r)} className="p-1.5 text-gray-400 hover:text-primary-500"><Edit2 size={16} /></button>
                    <button onClick={() => deleteResource(r.id)} className="p-1.5 text-gray-400 hover:text-red-500"><Trash2 size={16} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {resources.length === 0 && <p className="text-center text-gray-400 py-8">Nicio resursă adăugată</p>}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-lg">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-lg font-semibold">{editId ? 'Editare Resursă' : 'Adaugă Resursă'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nume *</label>
                <input type="text" required value={form.name} onChange={e => setForm({...form, name: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tip</label>
                  <select value={form.type} onChange={e => setForm({...form, type: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none">
                    {TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select value={form.status} onChange={e => setForm({...form, status: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none">
                    <option value="available">Disponibil</option>
                    <option value="in_use">În uz</option>
                    <option value="maintenance">Mentenanță</option>
                    <option value="out_of_stock">Epuizat</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cantitate</label>
                  <input type="number" min={0} value={form.quantity} onChange={e => setForm({...form, quantity: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cantitate minimă</label>
                  <input type="number" min={0} value={form.min_quantity} onChange={e => setForm({...form, min_quantity: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Locație</label>
                <input type="text" value={form.location} onChange={e => setForm({...form, location: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descriere</label>
                <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} rows={2}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
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

export default AdminResources;
