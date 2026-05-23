import type {
  Corridor,
  ForecastResponse,
  ExplainResponse,
  WhatifResponse,
  QuestionType,
} from './types';

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  getCorridors: () => get<Corridor[]>('/api/corridors'),

  getCorridor: (id: number) => get<Corridor>(`/api/corridors/${id}`),

  chat: (
    message: string,
    corridor_id: number,
    question_type: QuestionType,
    options?: { model?: string; refine?: boolean; charts?: boolean }
  ) =>
    post<{
      answer: string;
      question_type: string;
      corridor_name: string;
      model: string;
      sources: { label: string; type: string }[];
      chart_data: import('./types').ChartData | null;
    }>(
      '/api/chat',
      { message, corridor_id, question_type, ...options }
    ),

  forecast: (corridor_id: number, horizon: number) =>
    post<ForecastResponse>('/api/forecast', { corridor_id, horizon }),

  explain: (corridor_id: number, year: number, month: number) =>
    post<ExplainResponse>('/api/explain', { corridor_id, year, month }),

  whatif: (params: {
    corridor_id: number;
    wx_rain_mm_sum: number;
    wx_temp_c_mean: number;
    flt_total_pax: number;
    cal_n_holidays: number;
    cal_n_events: number;
  }) => post<WhatifResponse>('/api/whatif', params),
};

export function ttrColor(ttr: number): string {
  if (ttr < 1.15) return '#22c55e';
  if (ttr < 1.35) return '#eab308';
  if (ttr < 1.55) return '#f97316';
  return '#ef4444';
}

export function ttrLabel(ttr: number): string {
  if (ttr < 1.15) return 'Smooth';
  if (ttr < 1.35) return 'Moderate';
  if (ttr < 1.55) return 'Congested';
  return 'Very congested';
}

export function ttrBadgeClass(ttr: number): string {
  if (ttr < 1.15) return 'bg-green-500/20 text-green-400 border-green-500/30';
  if (ttr < 1.35) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
  if (ttr < 1.55) return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
  return 'bg-red-500/20 text-red-400 border-red-500/30';
}
