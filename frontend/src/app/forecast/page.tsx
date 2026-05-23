'use client';

import { useState, useEffect } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { api, ttrColor, ttrLabel, ttrBadgeClass } from '@/lib/api';
import type { Corridor, ForecastResponse } from '@/lib/types';
import { TrendingUp, RefreshCw } from 'lucide-react';

const HORIZONS = [
  { label: '3 months', value: 3 },
  { label: '6 months', value: 6 },
  { label: '12 months', value: 12 },
];

export default function ForecastPage() {
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [corridorId, setCorridorId] = useState(0);
  const [horizon, setHorizon] = useState(6);
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getCorridors().then(setCorridors).catch(console.error);
  }, []);

  const run = async () => {
    setLoading(true);
    try {
      const res = await api.forecast(corridorId, horizon);
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { run(); }, [corridorId, horizon]); // eslint-disable-line

  const corridor = corridors.find((c) => c.id === corridorId);

  const chartData = data?.predictions.map((p) => ({
    name: p.label,
    TTR: p.tt_ratio,
    AM: p.tt_ratio_am,
    PM: p.tt_ratio_pm,
    'Off-peak': p.tt_ratio_offpeak,
    CI_low: p.confidence_lower,
    CI_high: p.confidence_upper,
  })) ?? [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Traffic Forecast</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Predicted Travel Time Ratio (TTR) by time horizon
          </p>
        </div>
        <button onClick={run} disabled={loading} className="btn-secondary">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 items-end">
        <div>
          <label className="label">Corridor</label>
          <select
            value={corridorId}
            onChange={(e) => setCorridorId(Number(e.target.value))}
            className="select"
          >
            {corridors.map((c) => (
              <option key={c.id} value={c.id}>{c.name} — {c.description}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Time horizon</label>
          <div className="flex gap-1.5">
            {HORIZONS.map((h) => (
              <button
                key={h.value}
                onClick={() => setHorizon(h.value)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors
                  ${horizon === h.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700'
                  }`}
              >
                {h.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Summary bar */}
      {corridor && data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <SummaryCard label="Baseline TTR" value={data.baseline_tt_ratio.toFixed(3)} sub="current" />
          <SummaryCard
            label="Predicted TTR (avg.)"
            value={(data.predictions.reduce((s, p) => s + p.tt_ratio, 0) / data.predictions.length).toFixed(3)}
            sub={`over ${horizon} months`}
          />
          <SummaryCard
            label="Predicted peak"
            value={Math.max(...data.predictions.map((p) => p.tt_ratio)).toFixed(3)}
            highlight
          />
          <SummaryCard
            label="Corridor PTI"
            value={corridor.pti_mean.toFixed(2)}
            sub="avg (August 2024)"
          />
        </div>
      )}

      {/* Main chart */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={16} className="text-blue-400" />
          <h2 className="font-semibold text-slate-200 text-sm">
            Predicted TTR — {corridor?.name ?? '...'}
          </h2>
          {loading && (
            <span className="ml-auto text-xs text-slate-500 flex items-center gap-1.5">
              <RefreshCw size={11} className="animate-spin" /> Computing...
            </span>
          )}
        </div>

        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="ciGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} />
              <YAxis domain={[0.9, 'auto']} tick={{ fill: '#64748b', fontSize: 12 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                labelStyle={{ color: '#cbd5e1', fontWeight: 600 }}
                itemStyle={{ color: '#94a3b8' }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
              <ReferenceLine y={1.0} stroke="#475569" strokeDasharray="4 4" label={{ value: 'Free-flow', fill: '#475569', fontSize: 10 }} />
              <ReferenceLine y={1.5} stroke="#ef4444" strokeDasharray="4 4" strokeOpacity={0.4} />
              <Area type="monotone" dataKey="CI_high" stroke="none" fill="url(#ciGrad)" name="Upper CI" legendType="none" />
              <Area type="monotone" dataKey="CI_low"  stroke="none" fill="#0f172a" name="Lower CI" legendType="none" />
              <Area type="monotone" dataKey="TTR"    stroke="#3b82f6" strokeWidth={2.5} fill="none" dot={{ fill: '#3b82f6', r: 4 }} activeDot={{ r: 6 }} />
              <Area type="monotone" dataKey="AM"     stroke="#f97316" strokeWidth={1.5} fill="none" strokeDasharray="4 2" dot={false} />
              <Area type="monotone" dataKey="PM"     stroke="#ef4444" strokeWidth={1.5} fill="none" strokeDasharray="4 2" dot={false} />
              <Area type="monotone" dataKey="Off-peak" stroke="#22c55e" strokeWidth={1.5} fill="none" strokeDasharray="4 2" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-80 flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Table */}
      {data && (
        <div className="card overflow-hidden p-0">
          <div className="px-5 py-3 border-b border-slate-800">
            <h2 className="font-semibold text-slate-200 text-sm">Forecast details</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  {['Month', 'Overall TTR', 'AM peak', 'PM peak', 'Off-peak', '95% CI', 'Status'].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.predictions.map((p, i) => (
                  <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-2.5 font-medium text-slate-200">{p.label} {p.year}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-300">{p.tt_ratio.toFixed(3)}</td>
                    <td className="px-4 py-2.5 font-mono text-orange-400">{p.tt_ratio_am.toFixed(3)}</td>
                    <td className="px-4 py-2.5 font-mono text-red-400">{p.tt_ratio_pm.toFixed(3)}</td>
                    <td className="px-4 py-2.5 font-mono text-green-400">{p.tt_ratio_offpeak.toFixed(3)}</td>
                    <td className="px-4 py-2.5 text-xs text-slate-500 font-mono">
                      [{p.confidence_lower.toFixed(2)}, {p.confidence_upper.toFixed(2)}]
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`badge ${ttrBadgeClass(p.tt_ratio)}`}>
                        {ttrLabel(p.tt_ratio)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryCard({ label, value, sub, highlight }: { label: string; value: string; sub?: string; highlight?: boolean }) {
  return (
    <div className={`card ${highlight ? 'border-orange-500/30' : ''}`}>
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-2xl font-bold font-mono mt-1 ${highlight ? 'text-orange-400' : 'text-slate-100'}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  );
}
