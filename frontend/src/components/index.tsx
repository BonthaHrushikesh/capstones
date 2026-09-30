import React from 'react';

const paths = {
  overview: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
  analytics: <><path d="M4 19V5M4 19h17"/><path d="m7 15 4-5 3 2 5-7"/></>,
  anomaly: <><path d="M12 3 2.8 19h18.4L12 3Z"/><path d="M12 9v4m0 3h.01"/></>,
  forecast: <><path d="M3 17c3-8 5 3 8-4s5 2 10-7"/><path d="M16 6h5v5"/></>,
  copilot: <><path d="M12 3 4 13h6l-1 8 11-12h-7l-1-6Z"/></>,
  insight: <><path d="M9 18h6m-5 3h4"/><path d="M8 14a7 7 0 1 1 8 0c-1 .7-1 2-1 2h-6s0-1.3-1-2Z"/></>,
  reports: <><path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7m-7 4h7"/></>,
  quality: <><path d="m12 3 8 3v5c0 5-3.4 8.2-8 10-4.6-1.8-8-5-8-10V6l8-3Z"/><path d="m9 12 2 2 4-4"/></>,
  refresh: <><path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M5.5 9A7 7 0 0 1 18 6l2 6M4 12l2 6a7 7 0 0 0 12.5-3"/></>,
  calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></>,
  bell: <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></>,
  chevron: <path d="m8 10 4 4 4-4"/>,
  send: <><path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/></>,
  search: <><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/></>,
  download: <><path d="M12 3v12m-5-5 5 5 5-5"/><path d="M5 19v2h14v-2"/></>,
};

export function Icon({ name, size = 17 }) {
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name] || paths.overview}</svg>;
}

export function PageIntro({ eyebrow, title, text, action = null }) {
  return <div className="page-intro"><div><div className="eyebrow">{eyebrow}</div><h2>{title}</h2><p>{text}</p></div>{action}</div>;
}

export function Card({ title, subtitle = null, action = null, children = null, className = '' }) {
  return <section className={`card ${className}`}><div className="card-heading"><div>{title && <h3>{title}</h3>}{subtitle && <p>{subtitle}</p>}</div>{action}</div>{children}</section>;
}

export function Metric({ label, value, note, icon = 'analytics', tone = 'blue' }) {
  return <article className={`metric-card tone-${tone}`}><div className="metric-top"><span>{label}</span><span className="metric-icon"><Icon name={icon || 'analytics'} size={16}/></span></div><strong>{value ?? '--'}</strong>{note && <small>{note}</small>}</article>;
}

export function DateScope({ start, end, onStart, onEnd, onClear, label = 'Analysis period' }) {
  return <div className="date-scope">
    <span className="scope-label"><Icon name="calendar" size={15}/>{label}</span>
    <label>From<input aria-label="Start date" type="date" min="2006-12-16" max="2010-11-26" value={start} onChange={e => onStart(e.target.value)}/></label>
    <label>To<input aria-label="End date" type="date" min="2006-12-16" max="2010-11-26" value={end} onChange={e => onEnd(e.target.value)}/></label>
    <span className="scope-status" aria-live="polite">{start || end ? 'Applied across sections' : 'Full dataset'}</span>
    {onClear && <button type="button" className="btn secondary" onClick={onClear} disabled={!start && !end}>Reset</button>}
  </div>;
}

export function StatusMessage({ children, error = false }) {
  if (!children) return null;
  return <div className={`notice ${error ? 'notice-error' : ''}`}>{children}</div>;
}

export function EmptyState({ title = 'No results', text = 'Choose a date range and run the analysis.' }) {
  return <div className="empty-state"><span><Icon name="analytics" size={21}/></span><b>{title}</b><p>{text}</p></div>;
}

export function EnergyChart({ data, height = 300, anomalies = [] }) {
  const actual = data?.actual || [];
  const forecast = data?.forecast || [];
  if (!actual.length && !forecast.length) return <EmptyState title="No chart data" text="The selected range has no hourly readings."/>;
  const points = [...actual, ...forecast];
  const times = points.map(p => new Date(p.timestamp).getTime()).filter(Number.isFinite);
  const lowT = Math.min(...times), highT = Math.max(...times);
  const maxValue = Math.max(1, ...points.map(p => Number(p.kw) || 0)) * 1.16;
  const w = 900, h = 310, left = 54, right = 18, top = 20, bottom = 37;
  const x = t => left + ((new Date(t).getTime() - lowT) / Math.max(1, highT - lowT)) * (w - left - right);
  const y = v => top + (1 - v / maxValue) * (h - top - bottom);
  const path = list => list.map((p, i) => `${i ? 'L' : 'M'}${x(p.timestamp).toFixed(1)},${y(p.kw).toFixed(1)}`).join(' ');
  const actualPath = actual.length ? path(actual) : '';
  const forecastPath = forecast.length ? actual.length ? `M${x(actual.at(-1).timestamp).toFixed(1)},${y(actual.at(-1).kw).toFixed(1)} ${path(forecast).replace(/^M/, 'L')}` : path(forecast) : '';
  const ticks = [0, 1, 2, 3, 4];
  return <div className="energy-chart" style={{ height }}><svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Actual household demand, forecast, and anomaly candidates" preserveAspectRatio="none">
    {ticks.map(i => { const yy = top + i * (h - top - bottom) / 4; return <g key={i}><line x1={left} x2={w-right} y1={yy} y2={yy} className="chart-grid"/><text x={left-9} y={yy+4} textAnchor="end" className="chart-axis">{(maxValue * (1-i/4)).toFixed(1)}</text></g>; })}
    <path d={actualPath} className="actual-line"/><path d={forecastPath} className="forecast-line"/>
    {anomalies.map((point, i) => <circle key={`${point.timestamp}-${i}`} cx={x(point.timestamp)} cy={y(point.kw ?? point.observed_kw)} r="4.5" className="anomaly-point"><title>{point.timestamp} | {point.kw ?? point.observed_kw} kW | Anomaly candidate</title></circle>)}
    {actual.filter((_, i) => actual.length < 35 || i % Math.ceil(actual.length / 35) === 0).map(point => <circle key={point.timestamp} cx={x(point.timestamp)} cy={y(point.kw)} r="2.7" className="actual-point"><title>{point.timestamp} | Actual {point.kw} kW</title></circle>)}
    {forecast.map(point => <circle key={point.timestamp} cx={x(point.timestamp)} cy={y(point.kw)} r="2.5" className="forecast-point"><title>{point.timestamp} | Forecast {point.kw} kW</title></circle>)}
    {[0, .5, 1].map((ratio, i) => { const t = new Date(lowT + (highT-lowT)*ratio); return <text key={i} x={left + (w-left-right)*ratio} y={h-9} textAnchor={i===0?'start':i===2?'end':'middle'} className="chart-axis">{t.toLocaleDateString(undefined,{month:'short',day:'numeric'})} {t.toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit'})}</text>; })}
  </svg></div>;
}

export function Severity({ score }) {
  const level = Math.abs(score) >= 8 ? 'High' : Math.abs(score) >= 6 ? 'Medium' : 'Low';
  return <span className={`severity severity-${level.toLowerCase()}`}>{level}</span>;
}

