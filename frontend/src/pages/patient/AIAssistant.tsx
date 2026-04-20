import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { Send, Sparkles, Bot, User as UserIcon, AlertCircle, BookOpen, Calendar, Trash2 } from 'lucide-react';

interface BookingIntent {
  intent: 'book' | 'cancel' | null;
  specialty?: string | null;
  urgent?: boolean;
  date_hint?: 'today' | 'tomorrow' | 'this_week' | null;
  language?: string;
}

interface ChatMsg {
  role: 'user' | 'ai';
  content: string;
  category?: string;
  confidence?: number;
  related?: string[];
  booking?: BookingIntent;
}

const WELCOME_MSG: ChatMsg = {
  role: 'ai',
  content:
    'Bună ziua! Sunt asistentul medical AI. Pot răspunde la întrebări despre simptome, urgențe, prevenție, medicamente și sănătate generală în română și rusă. Cum vă pot ajuta?',
};

const STORAGE_PREFIX = 'aiChat_patient_';
const MAX_STORED_MSGS = 100;

const PatientAIAssistant: React.FC = () => {
  const { user } = useAuth();
  const storageKey = user ? `${STORAGE_PREFIX}${user.id}` : `${STORAGE_PREFIX}anon`;

  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState<ChatMsg[]>([WELCOME_MSG]);
  const [loading, setLoading] = useState(false);
  const [faq, setFaq] = useState<Record<string, string[]>>({});
  const endRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const goToBooking = (specialty?: string | null) => {
    if (specialty) {
      navigate(`/patient/book?specialty=${encodeURIComponent(specialty)}`);
    } else {
      navigate('/patient/book');
    }
  };

  // Load persisted chat on mount / when user changes
  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setHistory(parsed);
          return;
        }
      }
    } catch {
      // ignore corrupted storage
    }
    setHistory([WELCOME_MSG]);
  }, [storageKey]);

  // Persist whenever history changes (trim to last MAX_STORED_MSGS)
  useEffect(() => {
    try {
      const toStore = history.slice(-MAX_STORED_MSGS);
      localStorage.setItem(storageKey, JSON.stringify(toStore));
    } catch {
      // quota exceeded — fail silently
    }
  }, [history, storageKey]);

  const clearHistory = () => {
    if (!window.confirm('Ștergi întregul istoric al conversației cu AI?')) return;
    localStorage.removeItem(storageKey);
    setHistory([WELCOME_MSG]);
  };

  useEffect(() => {
    api.get('/ai/help/faq').then(res => setFaq(res.data.categories || {})).catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const ask = async (q: string) => {
    if (!q.trim() || loading) return;
    setHistory(prev => [...prev, { role: 'user', content: q }]);
    setQuestion('');
    setLoading(true);
    try {
      const res = await api.post('/ai/help/ask', { question: q });
      setHistory(prev => [
        ...prev,
        {
          role: 'ai',
          content: res.data.answer,
          category: res.data.category,
          confidence: res.data.confidence,
          related: res.data.related_questions || [],
          booking: res.data.booking_intent || undefined,
        },
      ]);
    } catch (e: any) {
      setHistory(prev => [
        ...prev,
        {
          role: 'ai',
          content:
            'Nu pot răspunde acum. Verificați conexiunea sau încercați mai târziu. În caz de urgență sunați 112.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const categoryLabels: Record<string, string> = {
    urgente: 'Urgențe',
    cardiologie: 'Cardiologie',
    neurologie: 'Neurologie',
    pneumologie: 'Pneumologie',
    gastroenterologie: 'Gastroenterologie',
    ortopedie: 'Ortopedie',
    pediatrie: 'Pediatrie',
    dermatologie: 'Dermatologie',
    sanatate_generala: 'Sănătate generală',
    preventie: 'Prevenție',
    sistem: 'Despre sistem',
    medicamente: 'Medicamente',
    sanatate_mintala: 'Sănătate mintală',
    programari: 'Programări',
  };

  const hasHistory = history.length > 1;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-primary-500 rounded-xl flex items-center justify-center">
            <Sparkles size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Asistent Medical AI</h1>
            <p className="text-sm text-gray-500">
              Antrenat pe 220+ întrebări medicale (RO + RU). Nu înlocuiește consultul medical.
            </p>
          </div>
        </div>
        {hasHistory && (
          <button
            onClick={clearHistory}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-red-50 hover:border-red-200 hover:text-red-600 transition"
            title="Șterge istoricul conversației"
          >
            <Trash2 size={16} /> Șterge istoric
          </button>
        )}
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 flex items-start gap-2">
        <AlertCircle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-amber-800">
          Informațiile sunt orientative. În caz de urgență sunați <strong>112</strong>.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Chat */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col h-[calc(100vh-16rem)]">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {history.map((m, i) => (
              <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {m.role === 'ai' && (
                  <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-primary-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot size={16} className="text-white" />
                  </div>
                )}
                <div className={`max-w-[75%] ${m.role === 'user' ? 'order-1' : ''}`}>
                  <div
                    className={`px-4 py-3 rounded-2xl ${
                      m.role === 'user'
                        ? 'bg-primary-500 text-white rounded-br-md'
                        : 'bg-gray-50 text-gray-800 rounded-bl-md border border-gray-100'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-line">{m.content}</p>
                  </div>
                  {m.role === 'ai' && m.category && (
                    <div className="flex items-center gap-2 mt-1 ml-2">
                      <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">
                        {categoryLabels[m.category] || m.category}
                      </span>
                      {typeof m.confidence === 'number' && m.confidence > 0 && (
                        <span className="text-xs text-gray-400">
                          Încredere: {Math.round(m.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  )}
                  {m.booking?.intent === 'book' && (
                    <div className="mt-2 ml-2">
                      <button
                        onClick={() => goToBooking(m.booking?.specialty)}
                        className="inline-flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-purple-500 to-primary-500 text-white text-sm rounded-lg hover:opacity-90 shadow-sm"
                      >
                        <Calendar size={14} />
                        {m.booking?.specialty
                          ? `Programează-te la ${m.booking.specialty}`
                          : 'Deschide programările'}
                      </button>
                    </div>
                  )}
                  {m.booking?.intent === 'cancel' && (
                    <div className="mt-2 ml-2">
                      <button
                        onClick={() => navigate('/patient/history')}
                        className="inline-flex items-center gap-2 px-3 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 shadow-sm"
                      >
                        <Calendar size={14} />
                        Vezi programările mele
                      </button>
                    </div>
                  )}
                  {m.related && m.related.length > 0 && (
                    <div className="mt-2 ml-2 space-y-1">
                      <p className="text-xs text-gray-500">Întrebări similare:</p>
                      {m.related.map((q, j) => (
                        <button
                          key={j}
                          onClick={() => ask(q)}
                          className="block text-left text-xs text-primary-600 hover:underline"
                        >
                          → {q}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {m.role === 'user' && (
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <UserIcon size={16} className="text-primary-600" />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-primary-500 rounded-full flex items-center justify-center">
                  <Bot size={16} className="text-white" />
                </div>
                <div className="bg-gray-50 px-4 py-3 rounded-2xl border border-gray-100">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <div className="p-4 border-t border-gray-100">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && ask(question)}
                placeholder="Întreabă orice despre sănătate..."
                className="flex-1 px-4 py-2 border border-gray-200 rounded-full focus:ring-2 focus:ring-primary-500 outline-none"
                disabled={loading}
              />
              <button
                onClick={() => ask(question)}
                disabled={loading || !question.trim()}
                className="p-2 bg-primary-500 text-white rounded-full hover:bg-primary-600 disabled:opacity-50"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>

        {/* Suggested topics */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 h-[calc(100vh-16rem)] overflow-y-auto">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen size={16} className="text-primary-500" />
            <h2 className="font-semibold text-gray-700">Subiecte sugerate</h2>
          </div>
          {Object.entries(faq).map(([cat, questions]) => (
            <div key={cat} className="mb-4">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                {categoryLabels[cat] || cat}
              </p>
              <div className="space-y-1">
                {questions.slice(0, 4).map((q, i) => (
                  <button
                    key={i}
                    onClick={() => ask(q)}
                    className="block text-left text-xs text-gray-600 hover:text-primary-600 hover:bg-primary-50 px-2 py-1 rounded w-full"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ))}
          {Object.keys(faq).length === 0 && (
            <p className="text-xs text-gray-400">Se încarcă subiectele...</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default PatientAIAssistant;
