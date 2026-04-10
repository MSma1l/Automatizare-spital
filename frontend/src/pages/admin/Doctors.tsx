import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { Plus, Edit2, UserCheck, UserX, X, Upload } from 'lucide-react';

const SPECIALTIES = [
  'Cardiologie', 'Neurologie', 'Ortopedie', 'Pediatrie', 'Dermatologie',
  'Oftalmologie', 'ORL', 'Chirurgie Generală', 'Medicină Internă',
  'Ginecologie', 'Urologie', 'Psihiatrie', 'Radiologie', 'Anestezie',
];

const DAYS = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică'];

const AdminDoctors: React.FC = () => {
  const [doctors, setDoctors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState({
    email: '', password: '', first_name: '', last_name: '',
    specialty: '', experience_years: 0, bio: '', phone: '', cabinet: '',
    schedules: [] as Array<{ day_of_week: number; start_time: string; end_time: string }>,
  });

  const fetchDoctors = () => {
    api.get('/admin/doctors')
      .then(res => setDoctors(res.data))
      .catch(() => toast.error('Eroare la încărcarea medicilor'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchDoctors(); }, []);

  const resetForm = () => {
    setForm({
      email: '', password: '', first_name: '', last_name: '',
      specialty: '', experience_years: 0, bio: '', phone: '', cabinet: '',
      schedules: [],
    });
    setEditId(null);
  };

  const openCreate = () => { resetForm(); setShowModal(true); };

  const openEdit = (doctor: any) => {
    setEditId(doctor.id);
    setForm({
      email: doctor.email || '', password: '',
      first_name: doctor.first_name, last_name: doctor.last_name,
      specialty: doctor.specialty, experience_years: doctor.experience_years,
      bio: doctor.bio || '', phone: doctor.phone || '', cabinet: doctor.cabinet || '',
      schedules: (doctor.schedules || []).map((s: any) => ({
        day_of_week: s.day_of_week, start_time: s.start_time, end_time: s.end_time,
      })),
    });
    setShowModal(true);
  };

  const addSchedule = () => {
    setForm(prev => ({
      ...prev,
      schedules: [...prev.schedules, { day_of_week: 0, start_time: '08:00', end_time: '16:00' }],
    }));
  };

  const removeSchedule = (idx: number) => {
    setForm(prev => ({
      ...prev,
      schedules: prev.schedules.filter((_, i) => i !== idx),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editId) {
        const { email, password, ...updateData } = form;
        await api.put(`/admin/doctors/${editId}`, updateData);
        toast.success('Medic actualizat');
      } else {
        await api.post('/admin/doctors', form);
        toast.success('Medic creat cu succes');
      }
      setShowModal(false);
      fetchDoctors();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Eroare');
    }
  };

  const toggleActive = async (doctorId: number) => {
    try {
      const res = await api.put(`/admin/doctors/${doctorId}/toggle-active`);
      toast.success(res.data.message);
      fetchDoctors();
    } catch {
      toast.error('Eroare la schimbarea statusului');
    }
  };

  const uploadPhoto = async (doctorId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      await api.post(`/admin/doctors/${doctorId}/photo`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      toast.success('Fotografie încărcată');
      fetchDoctors();
    } catch {
      toast.error('Eroare la încărcarea fotografiei');
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Gestionare Medici</h1>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition">
          <Plus size={18} /> Adaugă Medic
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Medic</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Specialitate</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Experiență</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Cabinet</th>
              <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase">Acțiuni</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {doctors.map(d => (
              <tr key={d.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center overflow-hidden">
                      {d.photo_url ? (
                        <img src={d.photo_url} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <span className="text-primary-600 font-medium">{d.first_name[0]}{d.last_name[0]}</span>
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">Dr. {d.first_name} {d.last_name}</p>
                      <p className="text-sm text-gray-400">{d.email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-600">{d.specialty}</td>
                <td className="px-6 py-4 text-gray-600">{d.experience_years} ani</td>
                <td className="px-6 py-4 text-gray-600">{d.cabinet || '-'}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${d.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {d.is_active ? 'Activ' : 'Inactiv'}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => openEdit(d)} className="p-1.5 text-gray-400 hover:text-primary-500 rounded" title="Editează">
                      <Edit2 size={16} />
                    </button>
                    <label className="p-1.5 text-gray-400 hover:text-primary-500 rounded cursor-pointer" title="Upload foto">
                      <Upload size={16} />
                      <input type="file" className="hidden" accept="image/*" onChange={(e) => {
                        if (e.target.files?.[0]) uploadPhoto(d.id, e.target.files[0]);
                      }} />
                    </label>
                    <button onClick={() => toggleActive(d.id)} className={`p-1.5 rounded ${d.is_active ? 'text-gray-400 hover:text-red-500' : 'text-gray-400 hover:text-green-500'}`} title={d.is_active ? 'Dezactivează' : 'Activează'}>
                      {d.is_active ? <UserX size={16} /> : <UserCheck size={16} />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {doctors.length === 0 && (
          <p className="text-center text-gray-400 py-8">Niciun medic adăugat</p>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-lg font-semibold">{editId ? 'Editare Medic' : 'Adaugă Medic'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {!editId && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                    <input type="email" required value={form.email} onChange={e => setForm({...form, email: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Parolă *</label>
                    <input type="password" required value={form.password} onChange={e => setForm({...form, password: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" minLength={6} />
                  </div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Prenume *</label>
                  <input type="text" required value={form.first_name} onChange={e => setForm({...form, first_name: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nume *</label>
                  <input type="text" required value={form.last_name} onChange={e => setForm({...form, last_name: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Specialitate *</label>
                  <select required value={form.specialty} onChange={e => setForm({...form, specialty: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none">
                    <option value="">Selectați</option>
                    {SPECIALTIES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Experiență (ani)</label>
                  <input type="number" min={0} value={form.experience_years} onChange={e => setForm({...form, experience_years: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Telefon</label>
                  <input type="tel" value={form.phone} onChange={e => setForm({...form, phone: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cabinet</label>
                  <input type="text" value={form.cabinet} onChange={e => setForm({...form, cabinet: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Biografie</label>
                <textarea value={form.bio} onChange={e => setForm({...form, bio: e.target.value})} rows={3}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
              </div>

              {/* Schedule */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">Program de lucru</label>
                  <button type="button" onClick={addSchedule} className="text-sm text-primary-500 hover:text-primary-600">+ Adaugă zi</button>
                </div>
                {form.schedules.map((s, idx) => (
                  <div key={idx} className="flex items-center gap-2 mb-2">
                    <select value={s.day_of_week} onChange={e => {
                      const newSchedules = form.schedules.map((item, i) =>
                        i === idx ? { ...item, day_of_week: parseInt(e.target.value) } : item
                      );
                      setForm({...form, schedules: newSchedules});
                    }} className="px-2 py-1.5 border rounded-lg text-sm">
                      {DAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
                    </select>
                    <input type="time" value={s.start_time} onChange={e => {
                      const newSchedules = form.schedules.map((item, i) =>
                        i === idx ? { ...item, start_time: e.target.value } : item
                      );
                      setForm({...form, schedules: newSchedules});
                    }} className="px-2 py-1.5 border rounded-lg text-sm" />
                    <span className="text-gray-400">-</span>
                    <input type="time" value={s.end_time} onChange={e => {
                      const newSchedules = form.schedules.map((item, i) =>
                        i === idx ? { ...item, end_time: e.target.value } : item
                      );
                      setForm({...form, schedules: newSchedules});
                    }} className="px-2 py-1.5 border rounded-lg text-sm" />
                    <button type="button" onClick={() => removeSchedule(idx)} className="text-red-400 hover:text-red-600"><X size={16} /></button>
                  </div>
                ))}
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 text-gray-600 border rounded-lg hover:bg-gray-50">Anulează</button>
                <button type="submit" className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600">
                  {editId ? 'Salvează' : 'Creează'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDoctors;
