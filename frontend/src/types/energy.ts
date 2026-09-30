export interface EnergyPoint {
  timestamp: string;
  kw: number;
}

export interface AnomalyCandidate {
  timestamp: string;
  observed_kw: number;
  baseline_kw: number;
  deviation_kw: number;
  score: number;
}

export interface ForecastResult {
  model: string;
  history_end: string;
  mean_kw: number;
  horizon_hours: number;
  forecast: EnergyPoint[];
  caveat: string;
}

export interface QueryEvidence {
  title: string;
  text: string;
  kind?: string;
}
