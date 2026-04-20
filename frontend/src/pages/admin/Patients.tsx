import React, { useEffect, useState, useRef } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { UserCheck, UserX, Eye, X, Plus, Sparkles, Camera, Upload } from 'lucide-react';

type PatientForm = {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  birth_date: string;
  gender: string;
  phone: string;
  address: string;
  insurance_number: string;
};

const emptyForm: PatientForm = {
  email: '', password: '', first_name: '', last_name: '',
  birth_date: '', gender: '', phone: '', address: '', insurance_number: '',
};

const AdminPatients: React.FC = () => {
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPatient, setSelectedPatient] = useState<any>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<PatientForm>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [showAI, setShowAI] = useState(false);
  const [aiImage, setAiImage] = useState<File | null>(null);
  const [aiImagePreview, setAiImagePreview] = useState<string>('');
  const [aiBusy, setAiBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

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

  const updateField = (field: keyof PatientForm, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload: any = { ...form };
      if (!payload.birth_date) delete payload.birth_date;
      if (!payload.gender) delete payload.gender;
      await api.post('/admin/patients', payload);
      toast.success('Pacient creat cu succes');
      setShowCreate(false);
      setForm(emptyForm);
      fetchPatients();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Eroare la crearea pacientului');
    } finally {
      setSaving(false);
    }
  };

  const handleImageSelected = (f: File | null) => {
    if (!f) return;
    if (!f.type.startsWith('image/')) {
      toast.error('Selectați un fișier imagine');
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      toast.error('Imagine prea mare (max 10MB)');
      return;
    }
    setAiImage(f);
    setAiImagePreview(URL.createObjectURL(f));
  };

  const clearAIImage = () => {
    if (aiImagePreview) URL.revokeObjectURL(aiImagePreview);
    setAiImage(null);
    setAiImagePreview('');
  };

  const runAIExtract = async () => {
    if (!aiImage) {
      toast.error('Încărcați o imagine a actului');
      return;
    }
    setAiBusy(true);
    try {
      const fd = new FormData();
      fd.append('file', aiImage);
      const res = await api.post('/ai/registration/parse-image', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const data = res.data.extracted || {};
      setForm(prev => ({
        ...prev,
        first_name: data.first_name || prev.first_name,
        last_name: data.last_name || prev.last_name,
        birth_date: data.birth_date || prev.birth_date,
        gender: data.gender || prev.gender,
        phone: data.phone || prev.phone,
        address: data.address || prev.address,
        insurance_number: data.insurance_number || prev.insurance_number,
        email: data.email || prev.email,
      }));
      const fieldsFound = res.data.fields_found || 0;
      if (fieldsFound === 0) {
        toast.error('AI nu a putut extrage date din imagine. Completați manual.');
      } else {
        toast.success(`AI a extras ${fieldsFound} câmpuri (încredere ${Math.round((res.data.confidence || 0) * 100)}%)`);
      }
      clearAIImage();
      setShowAI(false);
      setShowCreate(true);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Eroare la agentul AI');
    } finally {
      setAiBusy(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Gestionare Pacienți</h1>
        <div className="flex gap-2">
          <button onClick={() => { clearAIImage(); setShowAI(true); }}
            className="flex items-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition">
            <Sparkles size={18} /> Adaugă cu AI
          </button>
          <button onClick={() => { setForm(emptyForm); setShowCreate(true); }}
            className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition">
            <Plus size={18} /> Adaugă Pacient
          </button>
        </div>
      </div>

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

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-lg font-semibold">Adaugă Pacient</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                  <input type="email" required value={form.email}
                    onChange={e => updateField('email', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Parolă *</label>
                  <input type="password" required minLength={6} value={form.password}
                    onChange={e => updateField('password', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Prenume *</label>
                  <input type="text" required value={form.first_name}
                    onChange={e => updateField('first_name', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nume *</label>
                  <input type="text" required value={form.last_name}
                    onChange={e => updateField('last_name', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Data nașterii</label>
                  <input type="date" value={form.birth_date}
                    onChange={e => updateField('birth_date', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sex</label>
                  <select value={form.gender}
                    onChange={e => updateField('gender', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none">
                    <option value="">Selectați</option>
                    <option value="male">Masculin</option>
                    <option value="female">Feminin</option>
                    <option value="other">Altul</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Telefon</label>
                  <input type="tel" value={form.phone}
                    onChange={e => updateField('phone', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nr. asigurare</label>
                  <input type="text" value={form.insurance_number}
                    onChange={e => updateField('insurance_number', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Adresă</label>
                <input type="text" value={form.address}
                  onChange={e => updateField('address', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t">
                <button type="button" onClick={() => setShowCreate(false)}
                  className="px-4 py-2 text-gray-600 border rounded-lg hover:bg-gray-50">Anulează</button>
                <button type="submit" disabled={saving}
                  className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50">
                  {saving ? 'Se salvează...' : 'Creează'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* AI assist modal */}
      {showAI && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl">
            <div className="flex items-center justify-between p-6 border-b">
              <div className="flex items-center gap-2">
                <Sparkles size={20} className="text-purple-500" />
                <h2 className="text-lg font-semibold">Înregistrare Asistată AI</h2>
              </div>
              <button onClick={() => setShowAI(false)} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm text-gray-600">
                Faceți o fotografie a buletinului sau a cardului de asigurare, sau încărcați o imagine existentă.
                Agentul AI va rula OCR, va extrage datele (nume, data nașterii, telefon, adresă, asigurare)
                și va completa formularul automat.
              </p>

              {/* Hidden inputs */}
              <input ref={fileInputRef} type="file" accept="image/*" className="hidden"
                onChange={e => handleImageSelected(e.target.files?.[0] || null)} />
              <input ref={cameraInputRef} type="file" accept="image/*" capture="environment" className="hidden"
                onChange={e => handleImageSelected(e.target.files?.[0] || null)} />

              {!aiImagePreview ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <button type="button" onClick={() => cameraInputRef.current?.click()}
                    className="flex flex-col items-center justify-center gap-2 py-8 border-2 border-dashed border-purple-200 rounded-xl hover:bg-purple-50 transition">
                    <Camera size={36} className="text-purple-500" />
                    <span className="text-sm font-medium text-gray-700">Fă o fotografie</span>
                    <span className="text-xs text-gray-400">Folosește camera</span>
                  </button>
                  <button type="button" onClick={() => fileInputRef.current?.click()}
                    className="flex flex-col items-center justify-center gap-2 py-8 border-2 border-dashed border-purple-200 rounded-xl hover:bg-purple-50 transition">
                    <Upload size={36} className="text-purple-500" />
                    <span className="text-sm font-medium text-gray-700">Încarcă imagine</span>
                    <span className="text-xs text-gray-400">JPG, PNG (max 10MB)</span>
                  </button>
                </div>
              ) : (
                <div className="relative">
                  <img src={aiImagePreview} alt="Preview"
                    className="w-full max-h-72 object-contain rounded-lg border border-gray-200 bg-gray-50" />
                  <button type="button" onClick={clearAIImage}
                    className="absolute top-2 right-2 bg-white/90 hover:bg-white p-1.5 rounded-full shadow">
                    <X size={16} className="text-gray-700" />
                  </button>
                </div>
              )}

              <div className="flex justify-end gap-3">
                <button onClick={() => { clearAIImage(); setShowAI(false); }}
                  className="px-4 py-2 text-gray-600 border rounded-lg hover:bg-gray-50">Anulează</button>
                <button onClick={runAIExtract} disabled={aiBusy || !aiImage}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed">
                  <Sparkles size={16} /> {aiBusy ? 'Se procesează...' : 'Extrage și completează'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

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
