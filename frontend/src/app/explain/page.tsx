'use client';

import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import ReactMarkdown from 'react-markdown';
import { api } from '@/lib/api';
import type { Corridor, ExplainResponse } from '@/lib/types';
import { Microscope, RefreshCw } from 'lucide-react';

const MONTHS = [
  { label: 'January', value: 1 },  { label: 'February', value: 2 },
  { label: 'March', value: 3 },    { label: 'April', value: 4 },
  { label: 'May', value: 5 },      { label: 'June', value: 6 },
  { label: 'July', value: 7 },     { label: 'August', value: 8 },
  { label: 'September', value: 9 },{ label: 'October', value: 10 },
  { label: 'November', value: 11 },{ label: 'December', value: 12 },
];

export default function ExplainPage() {
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [corridorId, setCorridorId] = useState(0);
  const [year, setYear] = useState(2024);
  const [month, setMonth] = useState(1);
  const [data, setData] = useState<ExplainResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getCorridors().then(setCorridors).catch(console.error);
  }, []);

  const run = async () => {
    setLoading(true);
    try {
      const res = await api.explain(corridorId, year, month);
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, [corridorId, year, month]); // eslint-disable-line

  // Sort features by |shap_value|, keep sign for color
  const chartData = data?.shap_features
    .slice()
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .map((f) => ({ ...f, abs: Math.abs(f.shap_value) })) ?? [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Explainability (SHAP)</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Contribution of each feature to the predicted TTR — XGBoost + SHAP
          </p>
        </div>
        <button onClick={run} disabled={loading} className="btn-secondary">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Actualiser
        </button>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 items-end">
        <div>
          <label className="label">Corridor</label>
          <select value={corridorId} onChange={(e) => setCorridorId(Number(e.target.value))} className="select">
            {corridors.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Year</label>
          <select value={year} onChange={(e) => setYear(Number(e.target.value))} className="select">
            {[2022, 2023, 2024].map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Month</label>
          <select value={month} onChange={(e) => setMonth(Number(e.target.value))} className="select">
            {MONTHS.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-5">
        {/* SHAP chart — 3/5 */}
        <div className="xl:col-span-3 card">
          <div className="flex items-center gap-2 mb-1">
            <Microscope size={15} className="text-blue-400" />
            <h2 className="font-semibold text-slate-200 text-sm">SHAP values — top 10 features</h2>
            {loading && <RefreshCw size={11} className="ml-auto text-slate-500 animate-spin" />}
          </div>
          <p className="text-xs text-slate-600 mb-4">
            Positive value = increases TTR &nbsp;·&nbsp; Negative value = reduces TTR
          </p>

          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 0, right: 30, left: 10, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  tickFormatter={(v) => v.toFixed(2)}
                  domain={['auto', 'auto']}
                />
                <YAxis
                  dataKey="label"
                  type="category"
                  width={170}
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  formatter={(value: number) => [Number(value).toFixed(4), 'SHAP value']}
                  labelStyle={{ color: '#e2e8f0', fontWeight: 600, marginBottom: 4 }}
                  itemStyle={{ color: '#94a3b8' }}
                />
                <ReferenceLine x={0} stroke="#475569" />
                <Bar dataKey="shap_value" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={entry.shap_value >= 0 ? '#f97316' : '#22c55e'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-80 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {/* Legend */}
          <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-2 rounded-sm bg-orange-500 inline-block" />
              Increases congestion
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-2 rounded-sm bg-green-500 inline-block" />
              Reduces congestion
            </span>
          </div>
        </div>

        {/* Narrative + table — 2/5 */}
        <div className="xl:col-span-2 space-y-4">
          {/* LLM Narrative */}
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-5 h-5 rounded bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
                <span className="text-blue-400 text-[10px] font-bold">AI</span>
              </div>
              <h3 className="text-sm font-semibold text-slate-200">LLM Analysis</h3>
            </div>
            {data ? (
              <div className="prose-dark text-sm">
                <ReactMarkdown>{data.narrative}</ReactMarkdown>
              </div>
            ) : (
              <div className="h-24 flex items-center justify-center">
                <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>

          {/* Feature table */}
          {data && (
            <div className="card p-0 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800">
                <h3 className="text-sm font-semibold text-slate-200">Feature contributions</h3>
              </div>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="px-4 py-2 text-left text-slate-500 font-medium">Feature</th>
                    <th className="px-4 py-2 text-right text-slate-500 font-medium">SHAP</th>
                    <th className="px-4 py-2 text-right text-slate-500 font-medium">Rank</th>
                  </tr>
                </thead>
                <tbody>
                  {chartData.map((f, i) => (
                    <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                      <td className="px-4 py-2 text-slate-300">{f.label}</td>
                      <td className={`px-4 py-2 text-right font-mono font-medium ${f.shap_value >= 0 ? 'text-orange-400' : 'text-green-400'}`}>
                        {f.shap_value > 0 ? '+' : ''}{f.shap_value.toFixed(3)}
                      </td>
                      <td className="px-4 py-2 text-right text-slate-600">#{i + 1}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
