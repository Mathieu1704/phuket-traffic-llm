'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { api, ttrBadgeClass, ttrLabel } from '@/lib/api';
import type { Corridor } from '@/lib/types';
import { MapPin, Gauge, Clock, Route } from 'lucide-react';

const CorridorMap = dynamic(() => import('@/components/CorridorMap'), { ssr: false });

export default function Dashboard() {
  const [corridors, setCorridors] = useState<Corridor[]>([]);
  const [selected, setSelected] = useState<number | null>(null);

  useEffect(() => {
    api.getCorridors().then(setCorridors).catch(console.error);
  }, []);

  const active = corridors.find((c) => c.id === selected) ?? null;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
        <p className="text-sm text-slate-400 mt-0.5">
          4 road corridors — Phuket, Thailand · TomTom MOVE data (August 2024)
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {corridors.map((c) => (
          <button
            key={c.id}
            onClick={() => setSelected(selected === c.id ? null : c.id)}
            className={`card text-left transition-all duration-150 hover:border-slate-600 cursor-pointer
              ${selected === c.id ? 'border-blue-500/60 bg-blue-600/5' : ''}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div
                className="w-3 h-3 rounded-full mt-0.5 shrink-0"
                style={{ backgroundColor: c.color }}
              />
              <span className={`badge ${ttrBadgeClass(c.tt_ratio_am)}`}>
                {ttrLabel(c.tt_ratio_am)}
              </span>
            </div>

            <p className="font-semibold text-slate-100 text-sm leading-tight">{c.name}</p>
            <p className="text-xs text-slate-500 mt-0.5">{c.description}</p>

            <div className="mt-4 grid grid-cols-2 gap-y-2 gap-x-3">
              <Stat icon={<Gauge size={11} />} label="PTI" value={c.pti_mean.toFixed(2)} />
              <Stat icon={<Clock size={11} />} label="TTR AM" value={c.tt_ratio_am.toFixed(2)} />
              <Stat icon={<Route size={11} />} label="km" value={`${c.length_km}`} />
              <Stat icon={<Gauge size={11} />} label="km/h" value={`${c.spd_median_kmh}`} />
            </div>
          </button>
        ))}
      </div>

      {/* Map + Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Map */}
        <div className="lg:col-span-2 card p-0 overflow-hidden" style={{ height: '580px' }}>
          <CorridorMap
            corridors={corridors}
            selectedId={selected}
            onSelect={(id) => setSelected(selected === id ? null : id)}
          />
        </div>

        {/* Detail panel */}
        <div className="card space-y-4">
          {active ? (
            <>
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full shrink-0"
                  style={{ backgroundColor: active.color }}
                />
                <h2 className="font-semibold text-slate-100">{active.name}</h2>
              </div>
              <p className="text-xs text-slate-400">{active.name_th}</p>

              <div className="space-y-2">
                <Row label="Route" value={`N° ${active.route}`} />
                <Row label="Description" value={active.description} />
                <Row label="Length" value={`${active.length_km} km`} />
                <Row label="Average PTI" value={active.pti_mean.toFixed(2)} />
                <Row label="Max PTI" value={active.pti_max.toFixed(2)} />
                <Row label="Median speed" value={`${active.spd_median_kmh} km/h`} />
              </div>

              <div className="border-t border-slate-800 pt-3">
                <p className="text-xs text-slate-500 mb-2 uppercase tracking-wider font-medium">TTR by time period</p>
                <div className="space-y-2">
                  <TtrBar label="AM peak" value={active.tt_ratio_am} />
                  <TtrBar label="PM peak" value={active.tt_ratio_pm} />
                  <TtrBar label="Off-peak" value={active.tt_ratio_offpeak} />
                  <TtrBar label="Weekend" value={active.tt_ratio_weekend} />
                </div>
              </div>

              <div className="border-t border-slate-800 pt-3">
                <p className="text-xs text-slate-500 mb-2 uppercase tracking-wider font-medium">
                  {active.junctions.length} junctions
                </p>
                <div className="space-y-1">
                  {active.junctions.map((j, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <MapPin size={12} className="text-slate-500 mt-0.5 shrink-0" />
                      <div>
                        <p className="text-xs text-slate-300">{j.name}</p>
                        <p className="text-[10px] text-slate-600">{j.type}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center py-10 text-center">
              <MapPin size={28} className="text-slate-600 mb-3" />
              <p className="text-sm text-slate-500">Click on a corridor</p>
              <p className="text-xs text-slate-600 mt-1">on the map or KPI cards</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-1">
      <span className="text-slate-500">{icon}</span>
      <span className="text-[10px] text-slate-500">{label}</span>
      <span className="text-xs text-slate-200 font-medium ml-auto">{value}</span>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-xs text-slate-300 font-medium text-right">{value}</span>
    </div>
  );
}

function TtrBar({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, ((value - 1) / 1.5) * 100);
  const color = value < 1.15 ? '#22c55e' : value < 1.35 ? '#eab308' : value < 1.55 ? '#f97316' : '#ef4444';
  return (
    <div className="space-y-0.5">
      <div className="flex justify-between text-[10px]">
        <span className="text-slate-500">{label}</span>
        <span className="text-slate-300 font-mono">{value.toFixed(2)}</span>
      </div>
      <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
