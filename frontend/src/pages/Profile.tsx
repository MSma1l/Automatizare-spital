import React, { useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import {
  User as UserIcon, Mail, Lock, Camera, Save, Trash2,
  Phone, MapPin, Calendar, Shield, Stethoscope, CreditCard,
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';

type Tab = 'profile' | 'security' | 'photo';

const Profile: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [tab, setTab] = useState<Tab>('profile');
  const [me, setMe] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Profile fields
  const [form, setForm] = useState<any>({});
  const [saving, setSaving] = useState(false);

  // Email
  const [newEmail, setNewEmail] = useState('');
  const [emailPassword, setEmailPassword] = useState('');
  const [emailSaving, setEmailSaving] = useState(false);

  // Password
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwSaving, setPwSaving] = useState(false);

  // Photo
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const loadMe = async () => {
    setLoading(true);
    try {
      const res = await api.get('/me');
      setMe(res.data);
      setForm(res.data.profile || {});
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadMe(); }, []);

  const saveProfile = async () => {
    setSaving(true);
    try {
      const payload: any = {};
      for (const k of [
        'first_name', 'last_name', 'phone', 'birth_date', 'gender',
        'address', 'insurance_number', 'bio', 'specialty', 'cabinet', 'experience_years',
      ]) {
        if (form[k] !== undefined && form[k] !== null && form[k] !== '') payload[k] = form[k];
      }
      await api.put('/me', payload);
      toast.success('Profil actualizat');
      await loadMe();
      await refreshUser();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Eroare la salvare');
    } finally {
      setSaving(false);
    }
  };

  const changeEmail = async () => {
    if (!newEmail || !emailPassword) {
      toast.error('Completați toate câmpurile');
      return;
    }
    setEmailSaving(true);
    try {
      await api.put('/me/email', { new_email: newEmail, current_password: emailPassword });
      toast.success('Email actualizat');
      setNewEmail('');
      setEmailPassword('');
      await loadMe();
      await refreshUser();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Eroare la schimbarea emailului');
    } finally {
      setEmailSaving(false);
    }
  };

  const changePassword = async () => {
    if (!currentPassword || !newPassword) {
      toast.error('Completați toate câmpurile');
      return;
    }
    if (newPassword.length < 8) {
      toast.error('Parola nouă trebuie să aibă minim 8 caractere');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('Parolele noi nu coincid');
      return;
    }
    setPwSaving(true);
    try {
      await api.put('/me/password', { current_password: currentPassword, new_password: newPassword });
      toast.success('Parolă actualizată');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Eroare la schimbarea parolei');
    } finally {
      setPwSaving(false);
    }
  };

  const uploadPhoto = async (file: File) => {
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Fișierul este prea mare (max 5 MB)');
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      await api.post('/me/photo', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success('Fotografie actualizată');
      await loadMe();
      await refreshUser();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Upload eșuat');
    } finally {
      setUploading(false);
    }
  };

  const deletePhoto = async () => {
    try {
      await api.delete('/me/photo');
      toast.success('Fotografie ștearsă');
      await loadMe();
      await refreshUser();
    } catch {
      toast.error('Eroare la ștergere');
    }
  };

  if (loading || !me) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  const p = me.profile || {};
  const initials = `${(p.first_name || '?')[0] || ''}${(p.last_name || '')[0] || ''}`.toUpperCase();
  const roleLabels: Record<string, string> = { admin: 'Administrator', doctor: 'Medic', patient: 'Pacient' };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Profilul meu</h1>

      {/* Header card */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6">
        <div className="flex items-center gap-5 flex-wrap">
          <div className="relative">
            {p.photo_url ? (
              <img
                src={p.photo_url}
                alt="avatar"
                className="w-24 h-24 rounded-full object-cover border-4 border-primary-100"
              />
            ) : (
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary-400 to-purple-500 flex items-center justify-center text-white text-3xl font-bold">
                {initials || '?'}
              </div>
            )}
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className="absolute bottom-0 right-0 w-8 h-8 bg-white border border-gray-200 rounded-full flex items-center justify-center shadow hover:bg-gray-50"
              title="Schimbă fotografia"
            >
              <Camera size={14} className="text-gray-600" />
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg,image/gif"
              className="hidden"
              onChange={e => e.target.files?.[0] && uploadPhoto(e.target.files[0])}
            />
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-xl font-semibold text-gray-800">
              {p.first_name} {p.last_name}
            </p>
            <p className="text-sm text-gray-500 flex items-center gap-1 mt-0.5">
              <Mail size={14} /> {me.email}
            </p>
            <div className="flex items-center gap-2 mt-2">
              <span className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-primary-50 text-primary-700 rounded-full">
                <Shield size={12} /> {roleLabels[me.role] || me.role}
              </span>
              {p.specialty && (
                <span className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-purple-50 text-purple-700 rounded-full">
                  <Stethoscope size={12} /> {p.specialty}
                </span>
              )}
            </div>
          </div>

          {p.photo_url && (
            <button
              onClick={deletePhoto}
              className="flex items-center gap-1 text-sm text-red-600 hover:bg-red-50 px-3 py-2 rounded-lg"
            >
              <Trash2 size={14} /> Șterge fotografia
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 mb-4">
        {[
          { id: 'profile', label: 'Date personale', icon: <UserIcon size={16} /> },
          { id: 'security', label: 'Securitate', icon: <Lock size={16} /> },
          { id: 'photo', label: 'Fotografie', icon: <Camera size={16} /> },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id as Tab)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.id
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Profile tab */}
      {tab === 'profile' && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Prenume" icon={<UserIcon size={14} />}>
              <input
                type="text"
                value={form.first_name || ''}
                onChange={e => setForm({ ...form, first_name: e.target.value })}
                className="input-base"
              />
            </Field>
            <Field label="Nume" icon={<UserIcon size={14} />}>
              <input
                type="text"
                value={form.last_name || ''}
                onChange={e => setForm({ ...form, last_name: e.target.value })}
                className="input-base"
              />
            </Field>
            <Field label="Telefon" icon={<Phone size={14} />}>
              <input
                type="tel"
                value={form.phone || ''}
                onChange={e => setForm({ ...form, phone: e.target.value })}
                className="input-base"
                placeholder="+373 ..."
              />
            </Field>

            {me.role === 'patient' && (
              <>
                <Field label="Data nașterii" icon={<Calendar size={14} />}>
                  <input
                    type="date"
                    value={form.birth_date || ''}
                    onChange={e => setForm({ ...form, birth_date: e.target.value })}
                    className="input-base"
                  />
                </Field>
                <Field label="Sex" icon={<UserIcon size={14} />}>
                  <select
                    value={form.gender || ''}
                    onChange={e => setForm({ ...form, gender: e.target.value || null })}
                    className="input-base"
                  >
                    <option value="">—</option>
                    <option value="male">Masculin</option>
                    <option value="female">Feminin</option>
                    <option value="other">Altul</option>
                  </select>
                </Field>
                <Field label="Adresă" icon={<MapPin size={14} />} full>
                  <input
                    type="text"
                    value={form.address || ''}
                    onChange={e => setForm({ ...form, address: e.target.value })}
                    className="input-base"
                  />
                </Field>
                <Field label="Număr asigurare" icon={<CreditCard size={14} />}>
                  <input
                    type="text"
                    value={form.insurance_number || ''}
                    onChange={e => setForm({ ...form, insurance_number: e.target.value })}
                    className="input-base"
                  />
                </Field>
              </>
            )}

            {me.role === 'doctor' && (
              <>
                <Field label="Specialitate" icon={<Stethoscope size={14} />}>
                  <input
                    type="text"
                    value={form.specialty || ''}
                    onChange={e => setForm({ ...form, specialty: e.target.value })}
                    className="input-base"
                  />
                </Field>
                <Field label="Ani experiență">
                  <input
                    type="number"
                    min={0}
                    value={form.experience_years ?? 0}
                    onChange={e => setForm({ ...form, experience_years: parseInt(e.target.value, 10) || 0 })}
                    className="input-base"
                  />
                </Field>
                <Field label="Cabinet">
                  <input
                    type="text"
                    value={form.cabinet || ''}
                    onChange={e => setForm({ ...form, cabinet: e.target.value })}
                    className="input-base"
                  />
                </Field>
                <Field label="Bio" full>
                  <textarea
                    value={form.bio || ''}
                    onChange={e => setForm({ ...form, bio: e.target.value })}
                    rows={3}
                    className="input-base"
                  />
                </Field>
              </>
            )}
          </div>

          <div className="flex justify-end mt-5">
            <button
              onClick={saveProfile}
              disabled={saving}
              className="flex items-center gap-2 px-5 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50"
            >
              <Save size={16} /> {saving ? 'Se salvează...' : 'Salvează modificările'}
            </button>
          </div>
        </div>
      )}

      {/* Security tab */}
      {tab === 'security' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-800 mb-1 flex items-center gap-2">
              <Mail size={16} /> Schimbare email
            </h3>
            <p className="text-xs text-gray-500 mb-4">Email curent: <strong>{me.email}</strong></p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                type="email"
                placeholder="Email nou"
                value={newEmail}
                onChange={e => setNewEmail(e.target.value)}
                className="input-base"
              />
              <input
                type="password"
                placeholder="Parola curentă (pentru confirmare)"
                value={emailPassword}
                onChange={e => setEmailPassword(e.target.value)}
                className="input-base"
              />
            </div>
            <button
              onClick={changeEmail}
              disabled={emailSaving}
              className="mt-4 flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50"
            >
              <Save size={16} /> {emailSaving ? 'Se salvează...' : 'Actualizează email'}
            </button>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-800 mb-1 flex items-center gap-2">
              <Lock size={16} /> Schimbare parolă
            </h3>
            <p className="text-xs text-gray-500 mb-4">Parola nouă trebuie să aibă minim 8 caractere.</p>
            <div className="space-y-3 max-w-md">
              <input
                type="password"
                placeholder="Parola curentă"
                value={currentPassword}
                onChange={e => setCurrentPassword(e.target.value)}
                className="input-base"
              />
              <input
                type="password"
                placeholder="Parola nouă"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                className="input-base"
              />
              <input
                type="password"
                placeholder="Confirmă parola nouă"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                className="input-base"
              />
            </div>
            <button
              onClick={changePassword}
              disabled={pwSaving}
              className="mt-4 flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50"
            >
              <Save size={16} /> {pwSaving ? 'Se salvează...' : 'Actualizează parola'}
            </button>
          </div>
        </div>
      )}

      {/* Photo tab */}
      {tab === 'photo' && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <Camera size={16} /> Fotografie de profil
          </h3>
          <div className="flex items-center gap-6 flex-wrap">
            {p.photo_url ? (
              <img
                src={p.photo_url}
                alt="avatar"
                className="w-32 h-32 rounded-xl object-cover border border-gray-200"
              />
            ) : (
              <div className="w-32 h-32 rounded-xl bg-gray-100 flex items-center justify-center text-gray-400 text-4xl font-bold">
                {initials || '?'}
              </div>
            )}
            <div className="space-y-2">
              <button
                onClick={() => fileRef.current?.click()}
                disabled={uploading}
                className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50"
              >
                <Camera size={16} /> {uploading ? 'Se încarcă...' : 'Încarcă fotografie nouă'}
              </button>
              {p.photo_url && (
                <button
                  onClick={deletePhoto}
                  className="flex items-center gap-2 px-4 py-2 text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
                >
                  <Trash2 size={16} /> Șterge fotografia
                </button>
              )}
              <p className="text-xs text-gray-400">Formate acceptate: PNG, JPG, GIF. Max 5 MB.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const Field: React.FC<{
  label: string;
  icon?: React.ReactNode;
  full?: boolean;
  children: React.ReactNode;
}> = ({ label, icon, full, children }) => (
  <div className={full ? 'md:col-span-2' : ''}>
    <label className="flex items-center gap-1 text-xs font-medium text-gray-600 mb-1">
      {icon} {label}
    </label>
    {children}
  </div>
);

export default Profile;
