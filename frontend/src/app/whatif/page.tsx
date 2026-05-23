'use client';

import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';
import { api, ttrBadgeClass, ttrLabel, ttrColor } from '@/lib/api';
import type { Corridor, WhatifResponse } from '@/lib/types';
import { FlaskConical, Play } from 'lucide-react';

const SLIDERS = [
  { key: 'wx_rain_mm_sum',  label: 'Rainfall (mm)',        min: 0,   max: 500,    step: 10,    baseline: 150,    unit: 'mm' },
  { key: 'wx_temp_c_mean',  label: 'Temperature (°C)',     min: 22,  max: 36,     step: 0.5,   baseline: 29,     unit: '°C' },
  { key: 'flt_total_pax',   label: 'Flight passengers',    min: 50000, max: 250000, step: 5000, baseline: 120000, unit: 'k pax', scale: 1/1000, suffix: 'k' },
  { key: 'cal_n_holidays',  label: 'Public holidays',      min: 0,   max: 15,     step: 1,     baseline: 2,      unit: 'd' },
  { key: 'cal_n_events',    label: 'Local events',         min: 0,   max: 20,     step: 1,     baseline: 5,      unit: '' },
] as const;

type SliderKey = typeof SLIDERS[number]['key'];

type Params = {
  corridor_id: number;
  wx_rain_mm_sum: number;
  wx_temp_c_mean: number;
  flt_total_pax: number;
  cal_n_holidays: number;
  cal_n_events: number;
};

export default function WhatifPage() {
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [params, setParams] = useState<Params>({
    corridor_id: 0,
    wx_rain_mm_sum: 150,
    wx_temp_c_mean: 29,
    flt_total_pax: 120000,
    cal_n_holidays: 2,
    cal_n_events: 5,
  });
  const [result, setResult] = useState<WhatifResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getCorridors().then(setCorridors).catch(console.error);
  }, []);

  const run = async () => {
    setLoading(true);
    try {
      const res = await api.whatif(params);
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setParams((p) => ({
      ...p,
      wx_rain_mm_sum: 150,
      wx_temp_c_mean: 29,
      flt_total_pax: 120000,
      cal_n_holidays: 2,
      cal_n_events: 5,
    }));
    setResult(null);
  };

  const set = (key: SliderKey, value: number) =>
    setParams((p) => ({ ...p, [key]: value }));

  const factorChartData = result?.factors.map((f) => ({ name: f.label, Effet: f.effect })) ?? [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">What-if Analysis</h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Adjust parameters and observe the simulated impact on TTR
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-5">
        {/* Sliders — 2/5 */}
        <div className="xl:col-span-2 space-y-4">
          <div className="card">
            {/* Corridor */}
            <div className="mb-5">
              <label className="label">Corridor</label>
              <select
                value={params.corridor_id}
                onChange={(e) => setParams((p) => ({ ...p, corridor_id: Number(e.target.value) }))}
                className="select w-full"
              >
                {corridors.map((c) => (
                  <option key={c.id} value={c.id}>{c.name} — {c.description}</option>
                ))}
              </select>
            </div>

            {/* Sliders */}
            <div className="space-y-5">
              {SLIDERS.map((s) => {
                const val = params[s.key];
                const pct = ((val - s.min) / (s.max - s.min)) * 100;
                const displayVal = s.key === 'flt_total_pax'
                  ? `${Math.round(val / 1000)}k`
                  : s.key === 'wx_temp_c_mean'
                  ? `${val.toFixed(1)}°C`
                  : `${val}`;
                const baselinePct = ((s.baseline - s.min) / (s.max - s.min)) * 100;
                const changed = val !== s.baseline;

                return (
                  <div key={s.key}>
                    <div className="flex justify-between mb-1.5">
                      <label className="text-xs font-medium text-slate-400">{s.label}</label>
                      <div className="flex items-center gap-2">
                        {changed && (
                          <span className="text-[10px] text-slate-600">
                            baseline: {s.key === 'flt_total_pax' ? `${s.baseline / 1000}k` : s.baseline}{s.unit}
                          </span>
                        )}
                        <span className={`text-xs font-mono font-semibold ${changed ? 'text-blue-400' : 'text-slate-300'}`}>
                          {displayVal}
                        </span>
                      </div>
                    </div>
                    <div className="relative">
                      <input
                        type="range"
                        min={s.min}
                        max={s.max}
                        step={s.step}
                        value={val}
                        onChange={(e) => set(s.key, Number(e.target.value))}
                        className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-slate-700
                                   [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4
                                   [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full
                                   [&::-webkit-slider-thumb]:bg-blue-500 [&::-webkit-slider-thumb]:cursor-pointer"
                        style={{
                          background: `linear-gradient(to right, #3b82f6 ${pct}%, #334155 ${pct}%)`,
                        }}
                      />
                      {/* Baseline marker */}
                      <div
                        className="absolute top-0 w-0.5 h-1.5 bg-slate-500 rounded"
                        style={{ left: `${baselinePct}%`, transform: 'translateX(-50%)' }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Actions */}
            <div className="flex gap-2 mt-6">
              <button onClick={run} disabled={loading} className="btn-primary flex-1">
                {loading ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Play size={14} />
                )}
                Simulate
              </button>
              <button onClick={reset} className="btn-secondary">Reset</button>
            </div>
          </div>
        </div>

        {/* Results — 3/5 */}
        <div className="xl:col-span-3 space-y-4">
          {result ? (
            <>
              {/* TTR comparison */}
              <div className="card">
                <h2 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <FlaskConical size={14} className="text-blue-400" />
                  Simulation result — {result.corridor_name}
                </h2>
                <div className="grid grid-cols-3 gap-4">
                  <TTRCard label="Baseline" value={result.baseline_tt_ratio} />
                  <div className="flex items-center justify-center text-3xl font-light text-slate-600">
                    {result.pct_change > 0 ? '↑' : '↓'}
                  </div>
                  <TTRCard
                    label="Simulated"
                    value={result.predicted_tt_ratio}
                    highlight
                    delta={result.pct_change}
                  />
                </div>

                {/* Delta bar */}
                <div className="mt-5">
                  <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                    <span>Net impact</span>
                    <span className={`font-mono font-semibold ${result.delta > 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {result.delta > 0 ? '+' : ''}{result.delta.toFixed(4)} TTR
                    </span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${Math.min(100, Math.abs(result.pct_change) * 3)}%`,
                        backgroundColor: result.delta > 0 ? '#ef4444' : '#22c55e',
                        marginLeft: result.delta > 0 ? '0' : 'auto',
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* LLM narrative */}
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-5 h-5 rounded bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
                    <span className="text-blue-400 text-[10px] font-bold">AI</span>
                  </div>
                  <h3 className="text-sm font-semibold text-slate-200">LLM Interpretation</h3>
                </div>
                <div className="prose-dark text-sm">
                  <ReactMarkdown>{result.narrative}</ReactMarkdown>
                </div>
              </div>

              {/* Factor breakdown chart */}
              <div className="card">
                <h3 className="text-sm font-semibold text-slate-200 mb-4">Effect breakdown</h3>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={factorChartData} layout="vertical" margin={{ left: 10, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                    <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={(v) => v.toFixed(3)} />
                    <YAxis dataKey="name" type="category" width={140} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                      formatter={(v: number) => [`${v > 0 ? '+' : ''}${v.toFixed(4)}`, 'Δ TTR']}
                      labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                      itemStyle={{ color: '#94a3b8' }}
                    />
                    <Bar dataKey="Effet" radius={[0, 4, 4, 0]}>
                      {factorChartData.map((e, i) => (
                        <Cell key={i} fill={e.Effet >= 0 ? '#f97316' : '#22c55e'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : (
            <div className="card h-64 flex flex-col items-center justify-center gap-3 text-center">
              <FlaskConical size={32} className="text-slate-600" />
              <p className="text-sm text-slate-500">Adjust parameters and click <strong className="text-slate-400">Simulate</strong></p>
              <p className="text-xs text-slate-600">The model will calculate the impact of your assumptions on TTR</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TTRCard({ label, value, highlight, delta }: { label: string; value: number; highlight?: boolean; delta?: number }) {
  return (
    <div className={`rounded-xl p-4 text-center border ${highlight ? 'border-blue-500/30 bg-blue-600/5' : 'border-slate-700 bg-slate-800/50'}`}>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-3xl font-bold font-mono" style={{ color: ttrColor(value) }}>
        {value.toFixed(3)}
      </p>
      <span className={`badge mt-2 ${ttrBadgeClass(value)}`}>{ttrLabel(value)}</span>
      {delta !== undefined && (
        <p className={`text-xs font-mono mt-1.5 ${delta > 0 ? 'text-red-400' : 'text-green-400'}`}>
          {delta > 0 ? '+' : ''}{delta.toFixed(1)}%
        </p>
      )}
    </div>
  );
}
