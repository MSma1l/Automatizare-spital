import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0'];

const AdminReports: React.FC = () => {
  const [occupancy, setOccupancy] = useState<any[]>([]);
  const [appointments, setAppointments] = useState<any>(null);
  const [performance, setPerformance] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/admin/reports/occupancy'),
      api.get('/admin/reports/appointments'),
      api.get('/admin/reports/doctors-performance'),
    ]).then(([occ, appt, perf]) => {
      setOccupancy(occ.data);
      setAppointments(appt.data);
      setPerformance(perf.data);
    }).catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  const statusData = appointments ? Object.entries(appointments.by_status).map(([key, value]) => ({
    name: key === 'completed' ? 'Finalizate' : key === 'pending' ? 'În așteptare' : key === 'confirmed' ? 'Confirmate' : key === 'cancelled' ? 'Anulate' : key,
    value: value as number,
  })) : [];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Rapoarte</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Bed Occupancy */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-4">Ocupare Paturi pe Secții</h3>
          {occupancy.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={occupancy}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="ward" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="total" fill="#E3F2FD" name="Total" />
                <Bar dataKey="occupied" fill="#2196F3" name="Ocupate" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-8">Nu sunt date disponibile</p>
          )}
        </div>

        {/* Appointments by Status */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-4">Programări pe Status</h3>
          {statusData.length > 0 ? (
            <div className="flex items-center justify-center">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={statusData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label>
                    {statusData.map((_, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">Nu sunt programări</p>
          )}
          {appointments && (
            <p className="text-center text-sm text-gray-500 mt-2">Total: {appointments.total} programări</p>
          )}
        </div>
      </div>

      {/* Doctor Performance */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-700 mb-4">Performanță Medici</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Medic</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Specialitate</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Finalizate</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Anulate</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Rata completare</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Rating</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {performance.map(d => (
                <tr key={d.doctor_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-800">{d.name}</td>
                  <td className="px-4 py-3 text-gray-600">{d.specialty}</td>
                  <td className="px-4 py-3 text-center">{d.total_appointments}</td>
                  <td className="px-4 py-3 text-center text-green-600">{d.completed}</td>
                  <td className="px-4 py-3 text-center text-red-600">{d.cancelled}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`font-medium ${d.completion_rate >= 80 ? 'text-green-600' : d.completion_rate >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {d.completion_rate}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {d.avg_rating ? (
                      <span className="text-yellow-500">{'★'.repeat(Math.round(d.avg_rating))} {d.avg_rating}</span>
                    ) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {performance.length === 0 && <p className="text-center text-gray-400 py-8">Nu sunt date</p>}
        </div>
      </div>
    </div>
  );
};

export default AdminReports;
