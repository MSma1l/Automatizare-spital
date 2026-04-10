import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { useNavigate } from 'react-router-dom';
import { MessageSquare } from 'lucide-react';

const DoctorPatients: React.FC = () => {
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/doctor/patients')
      .then(res => setPatients(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const startChat = async (patientId: number) => {
    try {
      const res = await api.post(`/chat/conversations?target_id=${patientId}`);
      navigate('/doctor/chat', { state: { conversationId: res.data.conversation_id } });
    } catch {
      navigate('/doctor/chat');
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Pacienții Mei</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {patients.map(p => (
          <div key={p.id} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-primary-600 font-bold">
                    {p.first_name[0]}{p.last_name[0]}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-800">{p.first_name} {p.last_name}</p>
                  <p className="text-sm text-gray-500">{p.phone || 'Fără telefon'}</p>
                </div>
              </div>
              <button onClick={() => startChat(p.id)} className="p-2 text-gray-400 hover:text-primary-500 rounded-lg" title="Mesaj">
                <MessageSquare size={18} />
              </button>
            </div>
            <div className="mt-3 pt-3 border-t border-gray-50 text-sm text-gray-500">
              {p.last_appointment && (
                <p>Ultima vizită: {new Date(p.last_appointment).toLocaleDateString('ro-RO')}</p>
              )}
              {p.birth_date && <p>Data nașterii: {new Date(p.birth_date).toLocaleDateString('ro-RO')}</p>}
              {p.gender && <p>Sex: {p.gender === 'male' ? 'Masculin' : p.gender === 'female' ? 'Feminin' : 'Altul'}</p>}
            </div>
          </div>
        ))}
      </div>
      {patients.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <p>Nu aveți pacienți încă</p>
          <p className="text-sm mt-1">Pacienții vor apărea aici după prima programare</p>
        </div>
      )}
    </div>
  );
};

export default DoctorPatients;
