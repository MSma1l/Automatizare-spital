import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import {
  Sparkles, Activity, BedDouble, TrendingUp, Bell, Bot,
  Calendar, Users, Cpu, AlertCircle, CheckCircle2, RefreshCw,
} from 'lucide-react';

const iconForKey: Record<string, React.ReactNode> = {
  help: <Bot size={18} />,
  scheduling: <Calendar size={18} />,
  recommendation: <Users size={18} />,
  resource: <BedDouble size={18} />,
  monitoring: <Activity size={18} />,
  predictive: <TrendingUp size={18} />,
  notification: <Bell size={18} />,
};

const AdminAIAgents: React.FC = () => {
  const [agents, setAgents] = useState<any[]>([]);
  const [monitoring, setMonitoring] = useState<any>(null);
  const [predictions, setPredictions] = useState<any>(null);
  const [resources, setResources] = useState<any>(null);
  const [scheduling, setScheduling] = useState<any>(null);
  const [recs, setRecs] = useState<any>(null);
  const [aiHealthy, setAiHealthy] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([
      api.get('/ai/agents').then(r => r.data).catch(() => null),
      api.get('/ai/health').then(() => true).catch(() => false),
      api.get('/ai/monitoring').then(r => r.data).catch(() => null),
      api.get('/ai/predictions').then(r => r.data).catch(() => null),
      api.get('/ai/resources').then(r => r.data).catch(() => null),
      api.get('/ai/scheduling').then(r => r.data).catch(() => null),
      api.get('/ai/recommendations-all').then(r => r.data).catch(() => null),
    ]).then(([ag, h, mon, pred, res, sch, rc]) => {
      setAgents(ag?.agents || []);
      setAiHealthy(h);
      setMonitoring(mon);
      setPredictions(pred);
      setResources(res);
      setScheduling(sch);
      setRecs(rc);
    }).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-primary-500 rounded-xl flex items-center justify-center">
            <Cpu size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Agenți AI</h1>
            <p className="text-sm text-gray-500">
              7 agenți antrenați local (scikit-learn, fără API extern)
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {aiHealthy !== null && (
            <span className={`flex items-center gap-1 text-xs px-3 py-1 rounded-full ${
              aiHealthy ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {aiHealthy ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
              {aiHealthy ? 'Serviciu AI activ' : 'Serviciu AI offline'}
            </span>
          )}
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1 px-3 py-1 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Reîncarcă
          </button>
        </div>
      </div>

      {/* Agent cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {agents.map(a => (
          <div key={a.key} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-100 to-primary-100 rounded-lg flex items-center justify-center text-purple-600">
                {iconForKey[a.key] || <Sparkles size={18} />}
              </div>
              <div className="flex-1">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-gray-800">{a.name}</h3>
                  <span className="text-xs text-gray-400">{a.key}</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">{a.description}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {a.users.map((u: string) => (
                    <span key={u} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">
                      {u}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Live data sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Section
          title="MonitoringAgent — Status Resurse"
          icon={<Activity size={16} />}
          color="text-orange-600"
          data={monitoring}
        />
        <Section
          title="PredictiveAgent — Forecast Pacienți"
          icon={<TrendingUp size={16} />}
          color="text-blue-600"
          data={predictions}
        />
        <Section
          title="ResourceAllocationAgent — Paturi"
          icon={<BedDouble size={16} />}
          color="text-green-600"
          data={resources}
        />
        <Section
          title="SchedulingAgent — Conflicte"
          icon={<Calendar size={16} />}
          color="text-purple-600"
          data={scheduling}
        />
        <Section
          title="RecommendationAgent — Follow-up Global"
          icon={<Users size={16} />}
          color="text-pink-600"
          data={recs}
          fullWidth
        />
      </div>
    </div>
  );
};

const Section: React.FC<{
  title: string;
  icon: React.ReactNode;
  color: string;
  data: any;
  fullWidth?: boolean;
}> = ({ title, icon, color, data, fullWidth }) => (
  <div className={`bg-white rounded-xl p-5 shadow-sm border border-gray-100 ${fullWidth ? 'lg:col-span-2' : ''}`}>
    <div className={`flex items-center gap-2 mb-3 ${color}`}>
      {icon}
      <h3 className="font-semibold">{title}</h3>
    </div>
    {data ? (
      <pre className="text-xs bg-gray-50 p-3 rounded-lg overflow-auto max-h-64 text-gray-700">
        {JSON.stringify(data, null, 2)}
      </pre>
    ) : (
      <p className="text-sm text-gray-400">Fără date disponibile</p>
    )}
  </div>
);

export default AdminAIAgents;
