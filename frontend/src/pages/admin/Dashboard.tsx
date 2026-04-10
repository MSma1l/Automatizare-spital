import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { Users, BedDouble, Stethoscope, Calendar, Package, AlertTriangle } from 'lucide-react';

interface Stats {
  total_beds: number;
  occupied_beds: number;
  total_doctors: number;
  active_doctors: number;
  total_patients: number;
  appointments_today: number;
  low_stock_resources: number;
}

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/admin/stats')
      .then(res => setStats(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  if (!stats) return <p className="text-gray-500">Eroare la încărcarea datelor</p>;

  const cards = [
    { label: 'Total Paturi', value: stats.total_beds, sub: `${stats.occupied_beds} ocupate`, icon: <BedDouble size={24} />, color: 'bg-blue-500' },
    { label: 'Medici Activi', value: stats.active_doctors, sub: `din ${stats.total_doctors}`, icon: <Stethoscope size={24} />, color: 'bg-green-500' },
    { label: 'Total Pacienți', value: stats.total_patients, sub: 'înregistrați', icon: <Users size={24} />, color: 'bg-purple-500' },
    { label: 'Programări Azi', value: stats.appointments_today, sub: 'consultații', icon: <Calendar size={24} />, color: 'bg-orange-500' },
  ];

  const occupancyRate = stats.total_beds > 0
    ? Math.round(stats.occupied_beds / stats.total_beds * 100)
    : 0;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Dashboard Administrator</h1>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {cards.map((card) => (
          <div key={card.label} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-500">{card.label}</p>
                <p className="text-3xl font-bold text-gray-800 mt-1">{card.value}</p>
                <p className="text-xs text-gray-400 mt-1">{card.sub}</p>
              </div>
              <div className={`${card.color} p-3 rounded-lg text-white`}>
                {card.icon}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Occupancy overview */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-4">Ocupare Paturi</h3>
          <div className="flex items-center gap-4">
            <div className="relative w-24 h-24">
              <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none" stroke="#E5E7EB" strokeWidth="3"
                />
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none" stroke="#2196F3" strokeWidth="3"
                  strokeDasharray={`${occupancyRate}, 100`}
                />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-lg font-bold text-gray-700">
                {occupancyRate}%
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-600">
                <span className="font-medium text-gray-800">{stats.occupied_beds}</span> paturi ocupate
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium text-gray-800">{stats.total_beds - stats.occupied_beds}</span> paturi libere
              </p>
            </div>
          </div>
        </div>

        {/* Alerts */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-4">Alerte</h3>
          {stats.low_stock_resources > 0 ? (
            <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg">
              <AlertTriangle size={20} className="text-red-500" />
              <div>
                <p className="text-sm font-medium text-red-700">Stoc scăzut</p>
                <p className="text-xs text-red-600">{stats.low_stock_resources} resurse sub nivelul minim</p>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
              <Package size={20} className="text-green-500" />
              <p className="text-sm text-green-700">Toate resursele sunt la nivel optim</p>
            </div>
          )}
          {occupancyRate > 80 && (
            <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg mt-2">
              <AlertTriangle size={20} className="text-yellow-500" />
              <div>
                <p className="text-sm font-medium text-yellow-700">Ocupare ridicată</p>
                <p className="text-xs text-yellow-600">Ocuparea paturilor depășește 80%</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
