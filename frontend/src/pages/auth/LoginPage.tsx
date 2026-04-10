import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';
import { Stethoscope, Mail, Lock, Eye, EyeOff } from 'lucide-react';

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Autentificare reușită!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Eroare la autentificare');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-500 to-primary-700 p-12 flex-col justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
            <Stethoscope size={28} className="text-white" />
          </div>
          <span className="text-2xl font-bold text-white">Hospital DSS</span>
        </div>
        <div>
          <h1 className="text-4xl font-bold text-white mb-4">
            Sistem Inteligent de Sprijin Decizional
          </h1>
          <p className="text-xl text-primary-100">
            Gestionarea resurselor spitalicești cu ajutorul inteligenței artificiale
          </p>
        </div>
        <p className="text-primary-200 text-sm">
          &copy; 2026 Hospital DSS. Toate drepturile rezervate.
        </p>
      </div>

      {/* Right side - form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gray-50">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
              <Stethoscope size={22} className="text-white" />
            </div>
            <span className="text-xl font-bold text-gray-800">Hospital DSS</span>
          </div>

          <h2 className="text-2xl font-bold text-gray-800 mb-2">Bine ați revenit!</h2>
          <p className="text-gray-500 mb-8">Introduceți credențialele pentru a continua</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <div className="relative">
                <Mail size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="email@exemplu.ro"
                  required
                  className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Parolă</label>
              <div className="relative">
                <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Introduceți parola"
                  required
                  className="w-full pl-10 pr-12 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-primary-500 text-white font-medium rounded-lg hover:bg-primary-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Se conectează...' : 'Autentificare'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Nu aveți cont?{' '}
            <Link to="/register" className="text-primary-500 hover:text-primary-600 font-medium">
              Înregistrare pacient
            </Link>
          </p>

          {/* Demo credentials */}
          <div className="mt-8 p-4 bg-primary-50 rounded-lg">
            <p className="text-sm font-medium text-primary-700 mb-2">Conturi demo:</p>
            <p className="text-sm text-primary-600">Admin: admin@hospital.md / Admin123!</p>
            <p className="text-sm text-primary-600">Medic: doctor@hospital.md / Doctor123!</p>
            <p className="text-sm text-primary-600">Pacient: patient@hospital.md / Patient123!</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
