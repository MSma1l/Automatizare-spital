import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { Search, Star, Calendar, Clock, ArrowLeft } from 'lucide-react';

const BookAppointment: React.FC = () => {
  const [doctors, setDoctors] = useState<any[]>([]);
  const [specialties, setSpecialties] = useState<string[]>([]);
  const [filterSpecialty, setFilterSpecialty] = useState('');
  const [selectedDoctor, setSelectedDoctor] = useState<any>(null);
  const [selectedDate, setSelectedDate] = useState('');
  const [slots, setSlots] = useState<any[]>([]);
  const [selectedSlot, setSelectedSlot] = useState('');
  const [appointmentType, setAppointmentType] = useState('consultation');
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get('/patient/doctors'),
      api.get('/appointments/specialties'),
    ]).then(([d, s]) => {
      setDoctors(d.data);
      setSpecialties(s.data);
    }).catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filteredDoctors = filterSpecialty
    ? doctors.filter(d => d.specialty === filterSpecialty)
    : doctors;

  const fetchSlots = async (doctorId: number, date: string) => {
    try {
      const res = await api.get(`/patient/doctors/${doctorId}/available-slots?date_str=${date}`);
      setSlots(res.data);
    } catch {
      setSlots([]);
    }
  };

  const handleDateChange = (date: string) => {
    setSelectedDate(date);
    setSelectedSlot('');
    if (selectedDoctor && date) {
      fetchSlots(selectedDoctor.id, date);
    }
  };

  const handleBook = async () => {
    if (!selectedDoctor || !selectedDate || !selectedSlot) return;
    setBooking(true);
    try {
      await api.post('/patient/appointments', {
        doctor_id: selectedDoctor.id,
        date_time: `${selectedDate}T${selectedSlot}:00`,
        type: appointmentType,
      });
      toast.success('Programare creată cu succes!');
      setSelectedDoctor(null);
      setSelectedDate('');
      setSelectedSlot('');
      setSlots([]);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Eroare la programare');
    } finally {
      setBooking(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div></div>;
  }

  // Step 2: Select date and time
  if (selectedDoctor) {
    const DAYS = ['Duminică', 'Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă'];
    return (
      <div>
        <button onClick={() => setSelectedDoctor(null)} className="flex items-center gap-2 text-primary-500 hover:text-primary-600 mb-4">
          <ArrowLeft size={18} /> Înapoi la medici
        </button>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center overflow-hidden">
              {selectedDoctor.photo_url ? (
                <img src={selectedDoctor.photo_url} alt="" className="w-full h-full object-cover" />
              ) : (
                <span className="text-primary-600 font-bold text-xl">{selectedDoctor.first_name[0]}{selectedDoctor.last_name[0]}</span>
              )}
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-800">Dr. {selectedDoctor.first_name} {selectedDoctor.last_name}</h2>
              <p className="text-gray-500">{selectedDoctor.specialty} | {selectedDoctor.experience_years} ani experiență</p>
              {selectedDoctor.avg_rating && (
                <div className="flex items-center gap-1 mt-1">
                  <Star size={14} className="text-yellow-400 fill-yellow-400" />
                  <span className="text-sm text-gray-600">{selectedDoctor.avg_rating} ({selectedDoctor.review_count} recenzii)</span>
                </div>
              )}
            </div>
          </div>
          {selectedDoctor.bio && <p className="mt-3 text-sm text-gray-600">{selectedDoctor.bio}</p>}
          {selectedDoctor.schedules?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {selectedDoctor.schedules.map((s: any, i: number) => (
                <span key={i} className="text-xs bg-gray-100 px-2 py-1 rounded">
                  {DAYS[s.day_of_week === 6 ? 0 : s.day_of_week + 1]}: {s.start_time} - {s.end_time}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Date selection */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2"><Calendar size={18} /> Selectați Data</h3>
            <input
              type="date"
              value={selectedDate}
              min={new Date().toISOString().split('T')[0]}
              onChange={e => handleDateChange(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
            />

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Tip consultație</label>
              <select value={appointmentType} onChange={e => setAppointmentType(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none">
                <option value="consultation">Consultație</option>
                <option value="checkup">Control</option>
                <option value="video">Video consultație</option>
              </select>
            </div>
          </div>

          {/* Time slots */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2"><Clock size={18} /> Ore Disponibile</h3>
            {!selectedDate ? (
              <p className="text-gray-400 text-sm">Selectați mai întâi o dată</p>
            ) : slots.length === 0 ? (
              <p className="text-gray-400 text-sm">Nicio oră disponibilă în această zi</p>
            ) : (
              <div className="grid grid-cols-3 gap-2">
                {slots.map(s => (
                  <button
                    key={s.time}
                    disabled={!s.available}
                    onClick={() => setSelectedSlot(s.time)}
                    className={`py-2 px-3 rounded-lg text-sm font-medium transition ${
                      !s.available
                        ? 'bg-gray-100 text-gray-300 cursor-not-allowed'
                        : selectedSlot === s.time
                        ? 'bg-primary-500 text-white'
                        : 'bg-gray-50 text-gray-700 hover:bg-primary-50 hover:text-primary-600'
                    }`}
                  >
                    {s.time}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {selectedSlot && (
          <div className="mt-6 flex justify-center">
            <button
              onClick={handleBook}
              disabled={booking}
              className="px-8 py-3 bg-primary-500 text-white font-medium rounded-lg hover:bg-primary-600 transition disabled:opacity-50"
            >
              {booking ? 'Se programează...' : 'Confirmă Programarea'}
            </button>
          </div>
        )}
      </div>
    );
  }

  // Step 1: Select doctor
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Programare Consultație</h1>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input type="text" placeholder="Caută medic..." className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none" />
        </div>
        <select value={filterSpecialty} onChange={e => setFilterSpecialty(e.target.value)}
          className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 outline-none">
          <option value="">Toate specialitățile</option>
          {specialties.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {/* Doctor cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredDoctors.map(d => (
          <div key={d.id} onClick={() => setSelectedDoctor(d)}
            className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 cursor-pointer hover:border-primary-200 hover:shadow-md transition">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-14 h-14 bg-primary-100 rounded-full flex items-center justify-center overflow-hidden">
                {d.photo_url ? (
                  <img src={d.photo_url} alt="" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-primary-600 font-bold text-lg">{d.first_name[0]}{d.last_name[0]}</span>
                )}
              </div>
              <div>
                <p className="font-medium text-gray-800">Dr. {d.first_name} {d.last_name}</p>
                <p className="text-sm text-primary-500">{d.specialty}</p>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span>{d.experience_years} ani experiență</span>
              {d.avg_rating && (
                <span className="flex items-center gap-1">
                  <Star size={14} className="text-yellow-400 fill-yellow-400" />
                  {d.avg_rating}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
      {filteredDoctors.length === 0 && <p className="text-center text-gray-400 py-8">Niciun medic disponibil</p>}
    </div>
  );
};

export default BookAppointment;
