'use client';

import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { Send, Bot, User, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';
import type { Corridor, ChatMessage, QuestionType } from '@/lib/types';

const MODELS = [
  { id: 'phi3:mini',                    label: 'Phi-3 mini · 3.8B 🟢' },
  { id: 'llama3.1:8b-instruct-q4_K_M', label: 'Llama 3.1 · 8B 🟡' },
  { id: 'qwen2.5:14b',                  label: 'Qwen 2.5 · 14B 🔴' },
  { id: 'gpt-4o-mini',                  label: 'GPT-4o mini ☁️' },
];

const Q_TYPES: { id: QuestionType; label: string; example: string }[] = [
  { id: 'nowcast',  label: 'Nowcast',  example: "What is the current traffic situation?" },
  { id: 'forecast', label: 'Forecast', example: "What do you forecast for the next 3 months?" },
  { id: 'explain',  label: 'Explain',  example: "Why is congestion at this level?" },
  { id: 'whatif',   label: 'What-if',  example: "What if flights increased by 20%?" },
  { id: 'decision', label: 'Decision', example: "What is the best time to travel?" },
];

const SOURCE_COLORS: Record<string, string> = {
  traffic:           'bg-blue-500/20 text-blue-400',
  traffic_monthly:   'bg-blue-500/20 text-blue-400',
  traffic_segments:  'bg-blue-400/20 text-blue-300',
  flights:           'bg-green-500/20 text-green-400',
  weather:           'bg-cyan-500/20 text-cyan-400',
  social:            'bg-purple-500/20 text-purple-400',
  social_trends:     'bg-purple-500/20 text-purple-400',
  events:            'bg-orange-500/20 text-orange-400',
  poi:               'bg-pink-500/20 text-pink-400',
  intersections:     'bg-yellow-500/20 text-yellow-400',
  turning_movements: 'bg-amber-500/20 text-amber-400',
  transport:         'bg-teal-500/20 text-teal-400',
  weather_live:      'bg-cyan-400/30 text-cyan-300 ring-1 ring-cyan-400',
  flights_live:      'bg-green-400/30 text-green-300 ring-1 ring-green-400',
  tomtom_flow:       'bg-red-500/20 text-red-400 ring-1 ring-red-400',
};

export default function ChatPage() {
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [corridorId, setCorridorId] = useState(0);
  const [qType, setQType] = useState<QuestionType>('nowcast');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState('llama3.1:8b-instruct-q4_K_M');
  const [refine, setRefine] = useState(true);
  const [charts, setCharts] = useState(true);
  const [mounted, setMounted] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load persisted state after mount (avoids SSR hydration mismatch)
  useEffect(() => {
    try {
      const saved = localStorage.getItem('chat_messages');
      if (saved) setMessages(JSON.parse(saved));
      const cid = localStorage.getItem('chat_corridorId');
      if (cid) setCorridorId(Number(cid));
      const qt = localStorage.getItem('chat_qType');
      if (qt) setQType(qt as QuestionType);
      const m = localStorage.getItem('chat_model');
      if (m) setModel(m);
      const r = localStorage.getItem('chat_refine');
      if (r) setRefine(r !== 'false');
      const ch = localStorage.getItem('chat_charts');
      if (ch) setCharts(ch !== 'false');
    } catch { /* ignore */ }
    setMounted(true);
  }, []);

  useEffect(() => { if (mounted) localStorage.setItem('chat_messages',   JSON.stringify(messages));  }, [messages, mounted]);
  useEffect(() => { if (mounted) localStorage.setItem('chat_corridorId', String(corridorId));        }, [corridorId, mounted]);
  useEffect(() => { if (mounted) localStorage.setItem('chat_qType',      qType);                    }, [qType, mounted]);
  useEffect(() => { if (mounted) localStorage.setItem('chat_model',      model);                    }, [model, mounted]);
  useEffect(() => { if (mounted) localStorage.setItem('chat_refine',     String(refine));            }, [refine, mounted]);
  useEffect(() => { if (mounted) localStorage.setItem('chat_charts',     String(charts));            }, [charts, mounted]);

  useEffect(() => {
    api.getCorridors().then(setCorridors).catch(console.error);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;

    setInput('');
    setError(null);
    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setLoading(true);

    try {
      const res = await api.chat(msg, corridorId, qType, { model, refine, charts });
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.answer,
          question_type: res.question_type,
          sources: res.sources,
          chart_data: res.chart_data,
          model: res.model,
        },
      ]);
    } catch {
      setError("Unable to reach the API. Make sure the backend is running on :8000");
    } finally {
      setLoading(false);
    }
  };

  const selectedCorridor = corridors.find((c) => c.id === corridorId);

  return (
    <div className="flex h-screen">
      {/* Config panel */}
      <div className="w-64 shrink-0 bg-slate-900 border-r border-slate-800 p-4 flex flex-col gap-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-base font-semibold text-slate-100">LLM Chatbot</h1>
            <p className="text-xs text-slate-500 mt-0.5">Natural language questions</p>
          </div>
          {messages.length > 0 && (
            <button
              onClick={() => setMessages([])}
              className="text-[10px] px-2 py-0.5 rounded-md border border-slate-700 text-slate-400 hover:border-red-500/50 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Clear history"
            >
              Clear
            </button>
          )}
        </div>

        {/* Corridor selector */}
        <div>
          <label className="label">Corridor</label>
          <div className="space-y-1.5">
            {corridors.map((c) => (
              <button
                key={c.id}
                onClick={() => setCorridorId(c.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors
                  ${corridorId === c.id
                    ? 'bg-blue-600/20 border border-blue-500/30 text-blue-300'
                    : 'text-slate-400 hover:bg-slate-800 border border-transparent'
                  }`}
              >
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
                  <span className="font-medium">{c.name}</span>
                </div>
                <span className="text-[10px] text-slate-500 ml-4">{c.description}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Question type */}
        <div>
          <label className="label">Question type</label>
          <div className="space-y-1">
            {Q_TYPES.map((q) => (
              <button
                key={q.id}
                onClick={() => setQType(q.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors
                  ${qType === q.id
                    ? 'bg-slate-700 text-slate-100 font-medium'
                    : 'text-slate-400 hover:bg-slate-800'
                  }`}
              >
                {q.label}
              </button>
            ))}
          </div>
        </div>

        {/* Settings */}
        <div>
          <label className="label">Settings</label>
          <div className="space-y-2">
            {/* Model selector */}
            <div>
              <p className="text-[10px] text-slate-500 mb-1">Model</p>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
              >
                {MODELS.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>
            {/* Refine toggle */}
            <div className="flex items-center justify-between px-0.5">
              <p className="text-xs text-slate-400">Refine agent</p>
              <button
                onClick={() => setRefine((v) => !v)}
                className={`relative w-9 h-5 rounded-full transition-colors ${refine ? 'bg-blue-600' : 'bg-slate-700'}`}
              >
                <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${refine ? 'translate-x-4' : ''}`} />
              </button>
            </div>
            {/* Charts toggle */}
            <div className="flex items-center justify-between px-0.5">
              <p className="text-xs text-slate-400">Charts</p>
              <button
                onClick={() => setCharts((v) => !v)}
                className={`relative w-9 h-5 rounded-full transition-colors ${charts ? 'bg-blue-600' : 'bg-slate-700'}`}
              >
                <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${charts ? 'translate-x-4' : ''}`} />
              </button>
            </div>
          </div>
        </div>

        {/* Quick examples */}
        <div className="mt-auto">
          <label className="label">Example</label>
          <button
            onClick={() => send(Q_TYPES.find((q) => q.id === qType)?.example)}
            className="w-full text-left text-xs text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg px-3 py-2.5 transition-colors leading-relaxed"
          >
            {Q_TYPES.find((q) => q.id === qType)?.example}
          </button>
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Context bar */}
        {selectedCorridor && (
          <div className="shrink-0 px-5 py-2.5 bg-slate-900 border-b border-slate-800 flex items-center gap-3">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: selectedCorridor.color }} />
            <span className="text-sm text-slate-300 font-medium">{selectedCorridor.name}</span>
            <span className="text-xs text-slate-500">{selectedCorridor.description}</span>
            <span className="ml-auto text-xs text-slate-600 capitalize">{qType}</span>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center opacity-50">
              <Bot size={36} className="text-slate-500 mb-3" />
              <p className="text-sm text-slate-500">Ask a question about Phuket traffic</p>
              <p className="text-xs text-slate-600 mt-1">or click on the example in the left panel</p>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {m.role === 'assistant' && (
                <div className="w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot size={14} className="text-blue-400" />
                </div>
              )}

              <div className={`max-w-[75%] ${m.role === 'user' ? 'order-first' : ''}`}>
                <div
                  className={`rounded-2xl px-4 py-3 text-sm ${
                    m.role === 'user'
                      ? 'bg-blue-600 text-white rounded-tr-sm'
                      : 'bg-slate-800 border border-slate-700 text-slate-200 rounded-tl-sm'
                  }`}
                >
                  {m.role === 'assistant' ? (
                    <div className="prose-dark">
                      <ReactMarkdown>{m.content}</ReactMarkdown>
                    </div>
                  ) : (
                    m.content
                  )}
                </div>

                {m.model && (
                  <p className="text-[10px] text-slate-600 pl-1 mt-1.5">
                    via <span className="font-mono">{m.model}</span>
                  </p>
                )}

                {m.sources && (
                  <div className="flex flex-wrap gap-1.5 mt-1 pl-1 items-center">
                    {m.sources.some(s => s.type.endsWith('_live') || s.type === 'tomtom_flow') && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-red-500 text-white animate-pulse">
                        ● LIVE
                      </span>
                    )}
                    {m.sources.map((s, j) => (
                      <span
                        key={j}
                        className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${SOURCE_COLORS[s.type] ?? 'bg-slate-700 text-slate-400'}`}
                      >
                        {s.label}
                      </span>
                    ))}
                  </div>
                )}

                {m.chart_data && (
                  <div className="mt-3 bg-slate-900 border border-slate-700 rounded-xl p-3">
                    <p className="text-[11px] text-slate-400 mb-2 font-medium">{m.chart_data.title} <span className="text-slate-600">({m.chart_data.unit})</span></p>
                    <ResponsiveContainer width="100%" height={160}>
                      {m.chart_data.type === 'line' ? (
                        <LineChart data={m.chart_data.data}>
                          <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                          <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} width={35} />
                          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }} />
                          <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
                        </LineChart>
                      ) : (
                        <BarChart data={m.chart_data.data}>
                          <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                          <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} width={35} />
                          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }} />
                          <Bar dataKey="value" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                        </BarChart>
                      )}
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {m.role === 'user' && (
                <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                  <User size={14} className="text-slate-300" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shrink-0">
                <Bot size={14} className="text-blue-400" />
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex gap-1.5 items-center h-4">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 text-sm">
              <AlertCircle size={14} />
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="shrink-0 px-5 py-4 border-t border-slate-800 bg-slate-950">
          <form
            onSubmit={(e) => { e.preventDefault(); send(); }}
            className="flex gap-3"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`${qType} question about ${selectedCorridor?.name ?? '...'}`}
              disabled={loading}
              className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500
                         rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50
                         disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="btn-primary rounded-xl px-4"
            >
              <Send size={15} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
