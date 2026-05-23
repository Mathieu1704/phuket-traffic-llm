export interface Junction {
  name: string;
  lat: number;
  lon: number;
  type: string;
}

export interface Corridor {
  id: number;
  name: string;
  name_th: string;
  route: string;
  description: string;
  length_km: number;
  pti_mean: number;
  pti_max: number;
  tt_ratio_am: number;
  tt_ratio_pm: number;
  tt_ratio_offpeak: number;
  tt_ratio_weekend: number;
  spd_median_kmh: number;
  congestion_level: 'low' | 'moderate' | 'high' | 'very_high';
  status_label: string;
  tourist_access: boolean;
  color: string;
  polyline: [number, number][];
  junctions: Junction[];
}

export interface ChartData {
  type: 'bar' | 'line';
  title: string;
  data: { name: string; value: number }[];
  unit: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  question_type?: string;
  sources?: { label: string; type: string }[];
  chart_data?: ChartData | null;
  model?: string;
}

export interface ForecastPoint {
  label: string;
  month_num: number;
  year: number;
  tt_ratio: number;
  tt_ratio_am: number;
  tt_ratio_pm: number;
  tt_ratio_offpeak: number;
  confidence_lower: number;
  confidence_upper: number;
  congestion_level: string;
}

export interface ForecastResponse {
  corridor_id: number;
  corridor_name: string;
  horizon: number;
  baseline_tt_ratio: number;
  predictions: ForecastPoint[];
}

export interface ShapFeature {
  feature: string;
  label: string;
  shap_value: number;
}

export interface ExplainResponse {
  corridor_id: number;
  corridor_name: string;
  year: number;
  month: number;
  tt_ratio: number;
  shap_features: ShapFeature[];
  narrative: string;
}

export interface WhatifFactor {
  label: string;
  effect: number;
  baseline_val: number;
  sim_val: number;
}

export interface WhatifResponse {
  corridor_id: number;
  corridor_name: string;
  baseline_tt_ratio: number;
  predicted_tt_ratio: number;
  delta: number;
  pct_change: number;
  factors: WhatifFactor[];
  narrative: string;
}

export type QuestionType = 'nowcast' | 'forecast' | 'explain' | 'whatif' | 'decision';
