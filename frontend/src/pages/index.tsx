import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { api, saveEvaluation, safeRead, withRange } from '../services/api';
import { Card, DateScope, EmptyState, EnergyChart, Icon, Metric, PageIntro, Severity, StatusMessage } from '../components';
import { Header } from '../components/Header';
import { Sidebar } from '../components/Sidebar';
import { AgentWorkflow } from '../components/AgentWorkflow';

const NAV = [
  { id: 'overview', label: 'Overview', icon: 'overview' },
  { id: 'analytics', label: 'Energy Analytics', icon: 'analytics' },
  { id: 'anomaly', label: 'Anomaly Detection', icon: 'anomaly' },
  { id: 'forecast', label: 'Demand Forecast', icon: 'forecast' },
  { id: 'copilot', label: 'AI Copilot', icon: 'copilot' },
  { id: 'insights', label: 'Insights', icon: 'insight' },
  { id: 'reports', label: 'Reports', icon: 'reports' },
  { id: 'quality', label: 'Data Quality & Evaluation', icon: 'quality' },
];
const PAGE_META = {
  overview: ['Smart Grid Energy Intelligence', 'Historical household energy monitoring · 2006–2010'],
  analytics: ['Energy Analytics', 'Explore household demand and sub-meter usage'],
  anomaly: ['Anomaly Detection', 'Review unusual readings and supporting evidence'],
  forecast: ['Demand Forecast', 'Explore historical demand estimates and evaluation'],
  copilot: ['AI Copilot', 'Ask questions in natural language and inspect agent evidence'],
  insights: ['Energy Insights', 'Review findings and evidence from specialist agents'],
  reports: ['Reports', 'Generate and export historical household summaries'],
  quality: ['Data Quality & Evaluation', 'Review dataset readiness, forecast evaluation, and chat responses'],
};
const PERIODS = ['24h', '7d', '30d', '1y'];
const DEFAULT_SCOPE = { start: '', end: '' };
const DateRangeContext = createContext(null);

function requestError(error) { return error?.message || 'The request could not be completed.'; }
function useAsync(load, dependencies) {
  const [state, setState] = useState({ data: null, error: '', loading: true });
  useEffect(() => {
    let active = true;
    setState({ data: null, loading: true, error: '' });
    Promise.resolve().then(load).then(data => active && setState({ data, error: '', loading: false }))
      .catch(error => active && setState({ data: null, error: requestError(error), loading: false }));
    return () => { active = false; };
  // The caller passes stable scalar dependencies for each request.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
  return state;
}

function App() {
  const [view, setView] = useState('overview');
  const [refresh, setRefresh] = useState(0);
  const [ready, setReady] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [dateRange, setDateRange] = useState(DEFAULT_SCOPE);
  const [copilotSeed, setCopilotSeed] = useState('');
  const sharedDateRange = useMemo(() => ({
    ...dateRange,
    onStart: start => setDateRange(current => ({ ...current, start, end: current.end && current.end < start ? start : current.end })),
    onEnd: end => setDateRange(current => ({ ...current, start: end && current.start && current.start > end ? end : current.start, end })),
    onClear: () => setDateRange(DEFAULT_SCOPE),
  }), [dateRange]);
  const title = PAGE_META[view];
  useEffect(() => { api('/ready').then(() => setReady(true)).catch(() => setReady(false)); }, [refresh]);
  const refreshPage = () => setRefresh(value => value + 1);
  return <DateRangeContext.Provider value={sharedDateRange}><div className="react-app min-h-screen">
    <Header title={title[0]} subtitle={title[1]} ready={ready} onRefresh={refreshPage} onNavigate={setView}/>
    <div className="workspace">
      <Sidebar nav={NAV} view={view} ready={ready} expanded={sidebarOpen} onToggle={() => setSidebarOpen(value => !value)} onNavigate={setView}/>
      <main className="main-content" key={view}>
        {view === 'overview' && <Overview refresh={refresh} ready={ready} onAsk={(prompt='') => { setCopilotSeed(prompt); setView('copilot'); }}/>}
        {view === 'analytics' && <AnalyticsPage refresh={refresh}/>}
        {view === 'anomaly' && <AnomalyPage refresh={refresh}/>}
        {view === 'forecast' && <ForecastPage refresh={refresh}/>}
      {view === 'copilot' && <CopilotPage seedQuestion={copilotSeed}/>}
        {view === 'insights' && <InsightsPage refresh={refresh}/>}
        {view === 'reports' && <ReportsPage refresh={refresh}/>}
        {view === 'quality' && <EvaluationPage refresh={refresh}/>}
        <footer className="app-footer"><span>GridSense AI</span><span>Household analytics, not live grid telemetry</span></footer>
      </main>
    </div>
  </div></DateRangeContext.Provider>;
}

function useScope() {
  const scope = useContext(DateRangeContext);
  if (!scope) throw new Error('Date scope must be used inside the application date-range provider.');
  return { ...scope, applied: scope };
}

export function Overview({ refresh, onAsk, ready }) {
  const scope = useScope(); const [period, setPeriod] = useState('7d'); const [question, setQuestion] = useState('');
  const query = new URLSearchParams({ window: period });
  if (scope.applied.start) query.set('start', scope.applied.start);
  if (scope.applied.end) query.set('end', scope.applied.end);
  const { data, error, loading } = useAsync(async () => {
    const [summary, anomalies, forecast, trend] = await Promise.all([
      api(withRange('/api/summary', scope.applied.start, scope.applied.end)),
      api(`${withRange('/api/anomalies', scope.applied.start, scope.applied.end)}${scope.applied.start || scope.applied.end ? '&' : '?'}limit=100`),
      api(`${withRange('/api/forecast', scope.applied.start, scope.applied.end)}${scope.applied.start || scope.applied.end ? '&' : '?'}horizon=24`),
      api(`/api/trends?${query.toString()}`),
    ]);
    return { summary, anomalies, forecast, trend };
  }, [refresh, scope.applied.start, scope.applied.end, period]);
  function askOverview(event) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    onAsk(trimmed);
  }
  return <>
    <PageIntro eyebrow="HOUSEHOLD ENERGY / HISTORICAL DATA" title="Energy Intelligence Center" text="Track household demand, unusual readings, and historical trends." action={<span className={`pipeline-badge ${ready?'':'offline'}`}><i/>{ready?'Data service ready':'Checking data service'} <small>UCI household dataset · 2006–2010</small></span>}/>
    <DateScope {...scope}/>
    {error && <StatusMessage error>{error}</StatusMessage>}
    {loading && !data ? <Loading/> : data && <>
      <div className="metric-grid dashboard-metrics"><Metric label="AVERAGE DEMAND" value={`${data.summary.mean_kw} kW`} note="Hourly average in this period" icon="analytics"/><Metric label="PEAK DEMAND" value={`${data.summary.max_kw} kW`} note={data.summary.max_at?.replace('T',' ').slice(0,16)} icon="forecast" tone="indigo"/><Metric label="UNUSUAL READINGS" value={Number(data.anomalies.count).toLocaleString()} note="Candidates to review" icon="anomaly" tone="red"/><Metric label="NEXT 24H FORECAST" value={`${data.forecast.mean_kw} kW`} note="Forecast hourly average" icon="forecast" tone="violet"/></div>
      <Card title="Demand over time" subtitle={`${data.summary.start.slice(0,10)} to ${data.summary.end.slice(0,10)} Â· ${data.summary.hours.toLocaleString()} hourly observations`} className="chart-card" action={<div className="period-picker">{PERIODS.map(item => <button key={item} className={period===item?'active':''} onClick={() => setPeriod(item)}>{item.toUpperCase()}</button>)}</div>}>
        <div className="chart-legend"><span><i className="actual-swatch"/>Actual demand</span><span><i className="forecast-swatch"/>Forecast</span><span><i className="anomaly-swatch"/>Anomaly candidate</span></div>
        <EnergyChart data={data.trend} anomalies={data.trend.anomalies || []}/>
        <small className="chart-footnote">Hourly household active power. Forecast is based on the historical record, not live demand.</small>
      </Card>
      <InsightSpotlight anomaly={data.anomalies.flags?.[0]} method={data.anomalies.method} count={data.anomalies.count}/>
      <form onSubmit={askOverview} className="dashboard-ask"><span><Icon name="copilot" size={17}/><b>Ask about your energy</b></span><input aria-label="Ask about your energy data" value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask a question about your energy data"/><button className="btn primary" type="submit" disabled={!question.trim()}>Ask Copilot</button></form>
    </>}
  </>;
}

function InsightSpotlight({ anomaly, method, count }) {
  return <section className="insight-spotlight"><span className="spotlight-icon"><Icon name="insight" size={20}/></span><div className="spotlight-copy"><div className="eyebrow">AI ENERGY INSIGHT Â· EVIDENCE GROUNDED</div><h3>{anomaly ? 'A high-deviation hour is worth reviewing' : 'No anomaly candidates in this selected period'}</h3><p>{anomaly ? `The statistical screen ranked ${anomaly.timestamp.replace('T',' ').slice(0,16)} as unusual. A statistical candidate is not a confirmed equipment fault.` : 'No hours crossed the screening threshold. This does not establish that no equipment faults occurred.'}</p></div><div className="spotlight-evidence">{anomaly ? <><span>OBSERVED <b>{anomaly.observed_kw} kW</b></span><span>BASELINE <b>{anomaly.baseline_kw} kW</b></span><span>SCORE <b>{anomaly.score}</b></span></> : <><span>SCREENED <b>{Number(count||0).toLocaleString()} candidates</b></span><span>METHOD <b>{method || 'Statistical screen'}</b></span></>}</div></section>;
}

function AnswerCard({ result, onRate, onOpenChat }) {
  return <section className="overview-answer-card"><div className="answer-heading"><span className="bot-avatar"><Icon name="copilot" size={16}/></span><div><b>Evidence-backed answer</b><small>{result.llm?.used?'LLM phrasing grounded in local evidence':'Grounded local fallback'}</small></div><button className="text-button" onClick={onOpenChat}>Open Copilot â†’</button></div><p>{result.answer}</p><details><summary>Inspect answer trace</summary><div className="trace-list">{result.trace?.map((step,i)=><div key={`${step.agent}-${i}`}><b>{step.agent}</b><span>{step.finding}</span></div>)}</div></details><ResponseReview id={result.evaluationId} result={result} onRate={onRate}/></section>;
}

export function AnalyticsPage({ refresh }) {
  const scope = useScope(); const [showChart,setShowChart]=useState(false);
  const { data, error, loading } = useAsync(() => api(withRange('/api/summary', scope.applied.start, scope.applied.end)), [refresh, scope.applied.start, scope.applied.end]);
  return <><PageIntro eyebrow="AGENT 01 / ENERGY DATA ANALYST" title="Household demand profile" text="Explore demand, peaks, weekday patterns, and estimated sub-meter energy mix."/><DateScope {...scope}/>{error && <StatusMessage error>{error}</StatusMessage>}{loading && !data ? <Loading/> : data && <><div className="metric-grid"><Metric label="MEAN DEMAND" value={`${data.mean_kw} kW`} note="Hourly active power"/><Metric label="PEAK DEMAND" value={`${data.max_kw} kW`} note={data.max_at?.replace('T',' ')} icon="forecast" tone="indigo"/><Metric label="ENERGY IN PERIOD" value={`${Number(data.total_energy_kwh).toLocaleString()} kWh`} note={`${data.hours.toLocaleString()} hourly readings`} icon="analytics" tone="green"/><Metric label="HIGHEST AVERAGE WEEKDAY" value={data.top_weekday} note="Across selected history" icon="calendar" tone="violet"/></div><Card title="Estimated sub-meter energy mix" subtitle="Grouped meter readings estimate household areas; they do not identify individual appliances."><div className="mix-grid">{Object.entries(data.energy_mix_kwh || {}).map(([key,value],i)=><div className="mix-card" key={key}><span className={`mix-dot mix-${i%4}`}/><small>{key.replaceAll('_',' ')}</small><b>{Number(value).toLocaleString()} <em>kWh</em></b></div>)}</div></Card><Card title="Daily demand profile" subtitle="Daily mean active power; graph is available on request." action={<button className="btn secondary table-btn" onClick={()=>setShowChart(value=>!value)}>{showChart?'Hide graph':'Show graph'}</button>}>{showChart&&<EnergyChart height={280} data={{actual:data.daily.slice(-90).map(day=>({timestamp:day.date,kw:day.mean_kw})),forecast:[]}}/>}<div className="table-scroll"><DailyTable days={data.daily.slice(-30)}/></div></Card></>}</>;
}

export function AnomalyPage({ refresh }) {
  const scope = useScope(); const [selected, setSelected] = useState(null); const [showChart,setShowChart]=useState(false);
  const { data, error, loading } = useAsync(() => api(`${withRange('/api/anomalies', scope.applied.start, scope.applied.end)}${scope.applied.start||scope.applied.end?'&':'?'}limit=100`), [refresh, scope.applied.start, scope.applied.end]);
  const flags = data?.flags || [];
  const counts = useMemo(() => ({ high:flags.filter(x=>Math.abs(x.score)>=8).length, medium:flags.filter(x=>Math.abs(x.score)>=6&&Math.abs(x.score)<8).length, low:flags.filter(x=>Math.abs(x.score)<6).length }), [flags]);
  return <><PageIntro eyebrow="AGENT 02 / ANOMALY INVESTIGATOR" title="Unusual-hour review" text="Screen meter history for hours that differ from their usual weekday and time. Flags are investigation candidates, not confirmed faults."/><DateScope {...scope}/>{error&&<StatusMessage error>{error}</StatusMessage>}{loading&&!data?<Loading/>:data&&<><div className="metric-grid"><Metric label="TOTAL CANDIDATES" value={Number(data.count).toLocaleString()} note={`${Number(data.scope_hours||0).toLocaleString()} hours screened`} icon="anomaly" tone="red"/><Metric label="HIGH PRIORITY" value={counts.high} note="Among returned candidates" tone="red"/><Metric label="MEDIUM PRIORITY" value={counts.medium} note="Among returned candidates" tone="amber"/><Metric label="LOW PRIORITY" value={counts.low} note="Among returned candidates" tone="green"/></div><Card title="Anomaly timeline" subtitle={`Observed and expected demand for the highest ranked candidates Â· ${data.method}`} action={<button className="btn secondary table-btn" onClick={()=>setShowChart(value=>!value)}>{showChart?'Hide graph':'Show graph'}</button>}>{showChart&&<><div className="chart-legend"><span><i className="actual-swatch"/>Observed</span><span><i className="forecast-swatch"/>Expected baseline</span><span><i className="anomaly-swatch"/>Candidate</span></div><EnergyChart height={260} data={{actual:flags.map(item=>({timestamp:item.timestamp,kw:item.observed_kw})),forecast:flags.map(item=>({timestamp:item.timestamp,kw:item.baseline_kw}))}} anomalies={flags}/></>}<div className="table-scroll"><table><thead><tr><th>TIME</th><th>OBSERVED</th><th>EXPECTED</th><th>DEVIATION</th><th>SCORE</th><th>PRIORITY</th><th></th></tr></thead><tbody>{flags.map((item,i)=><React.Fragment key={item.timestamp}><tr className="click-row" onClick={()=>setSelected(selected===i?null:i)}><td>{item.timestamp.replace('T',' ').slice(0,16)}</td><td>{item.observed_kw.toFixed(3)} kW</td><td>{item.baseline_kw.toFixed(3)} kW</td><td>{(item.deviation_kw??item.observed_kw-item.baseline_kw).toFixed(3)} kW</td><td>{item.score}</td><td><Severity score={item.score}/></td><td><button className="btn table-btn" onClick={e=>{e.stopPropagation();setSelected(selected===i?null:i)}}>Inspect</button></td></tr>{selected===i&&<tr><td colSpan={7}><div className="detail-strip">{[['Previous hour',item.previous_hour_kw],['Previous day',item.previous_day_kw],['Previous week',item.previous_week_kw]].map(([label,value])=><span key={label}>{label}<b>{value==null?'Not available':`${value} kW`}</b></span>)}<small>Compare against meter or equipment records before taking action.</small></div></td></tr>}</React.Fragment>)}</tbody></table>{!flags.length&&<EmptyState title="No candidates in this period" text="No hours crossed the review threshold."/>}</div><div className="notice">Statistical flags are candidates for investigation, not verified equipment faults.</div></Card></>}</>;
}

export function ForecastPage({ refresh }) {
  const scope = useScope(); const [horizon,setHorizon]=useState(24);
  const { data, error, loading } = useAsync(async()=>{const [forecast,evaluation]=await Promise.all([api(`${withRange('/api/forecast',scope.applied.start,scope.applied.end)}${scope.applied.start||scope.applied.end?'&':'?'}horizon=${horizon}`),api(withRange('/api/evaluation',scope.applied.start,scope.applied.end)).catch(e=>({error:requestError(e)}))]);return {forecast,evaluation};},[refresh,scope.applied.start,scope.applied.end,horizon]);
  return <><PageIntro eyebrow="AGENT 03 / FORECAST SPECIALIST" title="Historical demand outlook" text="Generate a planning baseline from observed household demand. This is historical forecasting, not a live grid prediction." action={<label className="horizon-select">FORECAST HORIZON<select value={horizon} onChange={e=>setHorizon(Number(e.target.value))}>{[1,3,6,12,24].map(n=><option key={n} value={n}>{n} hour{n>1?'s':''}</option>)}</select></label>}/><DateScope {...scope}/>{error&&<StatusMessage error>{error}</StatusMessage>}{loading&&!data?<Loading/>:data&&<><div className="metric-grid"><Metric label="FORECAST MEAN" value={`${data.forecast.mean_kw} kW`} note={`${data.forecast.horizon_hours} hour horizon`} icon="forecast" tone="indigo"/><Metric label="PATTERN USED" value={data.forecast.model} note="Seasonal baseline with fallbacks" icon="analytics"/><Metric label="HISTORY ENDS" value={data.forecast.history_end.replace('T',' ').slice(0,16)} note="Latest observation used" icon="calendar" tone="green"/></div><Card title="Forecast values" subtitle={data.forecast.caveat}><div className="table-scroll"><table><thead><tr><th>FORECAST TIME</th><th>EXPECTED ACTIVE POWER</th></tr></thead><tbody>{data.forecast.forecast.map(item=><tr key={item.timestamp}><td>{item.timestamp.replace('T',' ')}</td><td>{item.kw.toFixed(3)} kW</td></tr>)}</tbody></table></div></Card><Card title="Chronological holdout evaluation" subtitle={data.evaluation.error||`${data.evaluation.model} Â· ${Number(data.evaluation.test_hours).toLocaleString()} test hours`}><div className="metric-grid compact"><Metric label="MAE" value={data.evaluation.mae_kw?`${data.evaluation.mae_kw} kW`:'--'} note="Mean absolute error"/><Metric label="RMSE" value={data.evaluation.rmse_kw?`${data.evaluation.rmse_kw} kW`:'--'} note="Root mean squared error"/><Metric label="MAPE" value={data.evaluation.mape_percent?`${data.evaluation.mape_percent}%`:'--'} note="Percentage error"/></div></Card></>}</>;
}

export function CopilotPage({ seedQuestion = '' }) {
  const scope = useScope();
  const [messages, setMessages] = useState(() => safeRead('gridsense.copilotConversation'));
  const [question, setQuestion] = useState(seedQuestion);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [searchBusy, setSearchBusy] = useState(false);
  const [searchError, setSearchError] = useState('');

  useEffect(() => {
    if (seedQuestion && !question) setQuestion(seedQuestion);
  }, [seedQuestion, question]);

  useEffect(() => {
    try { localStorage.setItem('gridsense.copilotConversation', JSON.stringify(messages.slice(-30))); } catch {}
  }, [messages]);

  async function askCopilot() {
    const askedQuestion = question.trim();
    if (!askedQuestion || busy) return;
    const context = messages.filter(message => message.role === 'user' && !message.pending).slice(-1)
      .map(message => `User: ${String(message.text || '').slice(0, 220)}`)
      .join('\n').slice(-550);

    setBusy(true);
    setError('');
    setQuestion('');
    setMessages(current => [...current,
      { role: 'user', text: askedQuestion, at: new Date().toISOString() },
      { role: 'assistant', text: 'Finding an answer from your energy data...', pending: true },
    ]);

    try {
      const result = await api('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: askedQuestion,
          start: scope.applied.start || null,
          end: scope.applied.end || null,
          context,
        }),
      });
      const evaluation = saveEvaluation(askedQuestion, result);
      setMessages(current => [...current.filter(message => !message.pending), {
        role: 'assistant', text: result.answer, at: new Date().toISOString(), result, evaluationId: evaluation.id,
      }]);
    } catch (err) {
      setError(requestError(err));
      setMessages(current => current.filter(message => !message.pending));
    } finally {
      setBusy(false);
    }
  }

  async function searchEvidence(event) {
    event.preventDefault();
    const query = searchQuery.trim();
    if (!query || searchBusy) return;
    const params = new URLSearchParams({ q: query, limit: '8' });
    if (scope.applied.start) params.set('start', scope.applied.start);
    if (scope.applied.end) params.set('end', scope.applied.end);
    setSearchBusy(true);
    setSearchError('');
    try {
      setSearchResult(await api(`/api/search?${params.toString()}`));
    } catch (err) {
      setSearchError(requestError(err));
      setSearchResult(null);
    } finally {
      setSearchBusy(false);
    }
  }

  function clearConversation() {
    setMessages([]);
    setError('');
    try { localStorage.removeItem('gridsense.copilotConversation'); } catch {}
  }

  const rangeLabel = scope.applied.start || scope.applied.end
    ? `Using ${scope.applied.start || 'the first available date'} to ${scope.applied.end || 'the latest available date'}.`
    : 'Using the full available dataset.';

  return <>
    <PageIntro eyebrow="ASK COPILOT" title="Energy Copilot" text="Ask a question, read the answer, and rate whether it helped." />
    <section className="card simple-copilot">
      <div className="simple-copilot-heading">
        <div><h3>Ask about your energy data</h3><p>{rangeLabel}</p></div>
        {messages.length > 0 && <button type="button" className="btn secondary" onClick={clearConversation}>Clear chat</button>}
      </div>
      <div className="message-list simple-message-list" role="log" aria-live="polite">
        {messages.length === 0 && <div className="welcome-message"><span className="bot-avatar"><Icon name="copilot" /></span><div><b>Ask your first question</b><p>For example: What were the peak demand hours?</p></div></div>}
        {messages.map((message, index) => <SimpleChatMessage key={`${message.at || 'pending'}-${index}`} message={message} />)}
      </div>
      <form className="chat-composer" onSubmit={event => { event.preventDefault(); askCopilot(); }}>
        <input value={question} onChange={event => setQuestion(event.target.value)} placeholder="Ask a question about your energy data..." aria-label="Question for Copilot" />
        <button className="btn primary" disabled={busy || !question.trim()}>{busy ? 'Answering...' : <><Icon name="send" size={15} /> Ask</>}</button>
      </form>
      {error && <StatusMessage error>{error}</StatusMessage>}
    </section>
    <section className="card keyword-search-panel">
      <div className="card-heading"><div><h3>Search energy evidence</h3><p>Find readings, analysis, forecast notes, and meter evidence by keyword. {rangeLabel}</p></div></div>
      <form className="keyword-search" onSubmit={searchEvidence}>
        <input value={searchQuery} onChange={event => setSearchQuery(event.target.value)} placeholder="Try voltage, peak hours, or sub-meter 2" aria-label="Search energy evidence by keyword" />
        <button className="btn secondary" disabled={searchBusy || !searchQuery.trim()}>{searchBusy ? 'Searching...' : <><Icon name="search" size={15} /> Search</>}</button>
      </form>
      {searchError && <StatusMessage error>{searchError}</StatusMessage>}
      {searchResult && <div className="search-hits" aria-live="polite">
        <p className="keyword-search-summary">{searchResult.result_count} match{searchResult.result_count === 1 ? '' : 'es'} for “{searchResult.query}”</p>
        {searchResult.results?.length ? searchResult.results.map((result, index) => <article key={`${result.kind}-${result.title}-${index}`}>
          <b>{result.title}</b><small>{result.kind} · relevance {result.score}</small><p>{result.text}</p>
          {result.matched_terms?.length > 0 && <div className="search-match-terms">Matched: {result.matched_terms.join(', ')}</div>}
        </article>) : <p>No matches found. Try a different energy or meter keyword.</p>}
      </div>}
    </section>
  </>;
}

function SimpleChatMessage({ message }) {
  if (message.pending) return <div className="message assistant"><span className="bot-avatar"><Icon name="copilot" size={15} /></span><div className="message-body">{message.text}<span className="typing-dots">Please wait...</span></div></div>;
  return <div className={`message ${message.role}`}><span className={message.role === 'assistant' ? 'bot-avatar' : 'user-avatar'}>{message.role === 'assistant' ? 'G' : 'You'}</span><div className="message-body">{message.text}{message.evaluationId && <CurrentQuestionReview id={message.evaluationId} />}</div></div>;
}

function CurrentQuestionReview({ id }) {
  const [rating, setRating] = useState(() => safeRead('gridsense.chatEvaluation').find(item => item.id === id)?.rating);
  function rate(value) { rateStoredResponse(id, value); setRating(value); }
  return <div className="response-review"><span>Was this answer helpful?</span><div><button type="button" onClick={() => rate('helpful')}>{rating === 'helpful' ? 'Helpful' : 'Yes'}</button><button type="button" onClick={() => rate('review')}>{rating === 'review' ? 'Needs review' : 'Needs improvement'}</button></div></div>;
}

function LegacyCopilotPage({ refresh, seedQuestion = '' }) {
  const scope=useScope();const [messages,setMessages]=useState(()=>safeRead('gridsense.reactConversation'));
  const [question,setQuestion]=useState(seedQuestion); const [busy,setBusy]=useState(false); const [error,setError]=useState('');
  const [llm,setLlm]=useState('Checking language model configuration...'); const [searchQuery,setSearchQuery]=useState(''); const [searchResult,setSearchResult]=useState(null); const [history,setHistory]=useState(()=>safeRead('gridsense.queryHistory'));
  useEffect(()=>{ if (seedQuestion && !question) setQuestion(seedQuestion); }, [seedQuestion, question]);
  useEffect(()=>{api('/api/llm-status').then(v=>setLlm(v.enabled?`LLM configured Â· ${v.model}`:'Grounded local fallback Â· no LLM key configured')).catch(()=>setLlm('Language model status unavailable'));},[refresh]);
  useEffect(()=>{try{localStorage.setItem('gridsense.reactConversation',JSON.stringify(messages.slice(-60)))}catch{/* The visible conversation still works if storage is full. */}},[messages]);
  async function sendQuestion(q=question) {
    if(!q.trim()||busy)return;
      const priorContext=messages.filter(message=>!message.pending).slice(-2).map(message=>`${message.role==='user'?'User':'Assistant'}: ${String(message.text||'').slice(0,220)}`).join('\n').slice(-550);
    setBusy(true); setError(''); setQuestion('');
    setMessages(current=>[...current,{role:'user',text:q,at:new Date().toISOString()},{role:'assistant',text:'Routing your question to the energy agents...',pending:true}]);
    try {
      const result=await api('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,start:scope.applied.start||null,end:scope.applied.end||null,context:priorContext})});
      const evaluation=saveEvaluation(q,result); const item={role:'assistant',text:result.answer,at:new Date().toISOString(),result,evaluationId:evaluation.id};
      setMessages(current=>[...current.filter(msg=>!msg.pending),item]);
      const previous=safeRead('gridsense.queryHistory');const next=[{q,at:new Date().toISOString()},...previous].slice(0,30);try{localStorage.setItem('gridsense.queryHistory',JSON.stringify(next))}catch{}setHistory(next);
    } catch(err) {
      const message=`I could not complete that request: ${requestError(err)}`;const evaluation=saveEvaluation(q,{answer:message,status:'request_failed'});
      setMessages(current=>[...current.filter(msg=>!msg.pending),{role:'assistant',text:message,at:new Date().toISOString(),evaluationId:evaluation.id}]);
    } finally {setBusy(false)}
  }
  function startNewChat(){setMessages([]);setError('');try{localStorage.setItem('gridsense.reactConversation','[]')}catch{}}
  const starterPrompts = ['What were the peak demand hours?', 'Which periods show unusual patterns?', 'Forecast demand for the next day', 'How much energy did the kitchen use?'];
  return <><PageIntro eyebrow="GRIDSENSE AI / NATURAL-LANGUAGE ASSISTANT" title="Energy Copilot" text="Ask about demand peaks, unusual readings, sub-meter usage, or historical forecasts. Answers show their evidence and agent trace." action={<div className="copilot-actions"><span className="provider-badge"><i/> {llm}</span><a className="btn secondary" href="/workflow-diagram.pdf" target="_blank" rel="noreferrer">Open workflow PDF</a></div>}/>
    <details className="copilot-workflow-details"><summary>How does Copilot build an answer?</summary><AgentWorkflow/></details>
    <div className="copilot-feature-grid">
      <article className="copilot-feature-card"><span className="feature-pill">Peak detection</span><h3>Identify load spikes</h3><p>Spot the strongest usage windows and compare them to your household baseline.</p></article>
      <article className="copilot-feature-card"><span className="feature-pill">Anomaly review</span><h3>Check suspicious hours</h3><p>Review statistically unusual readings and understand whether they are simply outliers or signals to inspect.</p></article>
      <article className="copilot-feature-card"><span className="feature-pill">Forecast planning</span><h3>Model next-demand outlook</h3><p>Ask for a short-horizon forecast and see how the historical trend is being interpreted.</p></article>
    </div>
    <section className="card copilot-panel"><div className="copilot-top"><div><h3>Ask GridSense</h3><p>Conversation is saved in this browser and can be reviewed in Evaluation.</p></div><button className="btn secondary" onClick={startNewChat}>New chat</button></div>
      <div className="copilot-hero">
        <div className="copilot-hero-copy"><span className="eyebrow-tag">AI assistance</span><h4>Ask questions in plain English</h4><p>Get evidence-backed answers from the analytics, anomaly, and forecasting specialists.</p></div>
        <div className="copilot-badges"><span>Evidence trace</span><span>Local data grounding</span><span>Context-aware answers</span></div>
      </div>
      <DateScope {...scope} label="Optional answer date scope"/>
      {messages.length===0&&<div className="suggestion-chips" style={{marginBottom:'12px'}}>{starterPrompts.map(text=><button key={text} disabled={busy} onClick={()=>sendQuestion(text)}>{text}</button>)}</div>}
      <div className="message-list" role="log" aria-live="polite">{messages.length===0?<div className="welcome-message"><span className="bot-avatar"><Icon name="copilot"/></span><div><b>Hi, I am GridSense.</b><p>Ask me about consumption, peaks, anomalies, forecasts, or the meaning of your meter data.</p></div></div>:messages.map((message,i)=><ChatMessage key={`${message.at}-${i}`} message={message} onRate={rateStoredResponse} onAsk={sendQuestion}/>)}</div>
      <form className="chat-composer" onSubmit={e=>{e.preventDefault();sendQuestion()}}><input value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Ask a question about household energy..."/><button className="btn primary" disabled={busy||!question.trim()}><Icon name="send" size={15}/>{busy?'Thinking':'Send'}</button></form>
      <details className="history-drawer"><summary>Recent question history ({history.length})</summary><div className="history-list">{history.length?history.map((item,i)=><button key={`${item.at}-${i}`} onClick={()=>sendQuestion(item.q)}><span>{item.q}</span><small>{item.at?new Date(item.at).toLocaleDateString():''}</small></button>):<p>No saved question history yet.</p>}</div></details>
      <details className="history-drawer"><summary>Search energy evidence by keyword</summary><form className="keyword-search" onSubmit={async e=>{e.preventDefault();try{const params=new URLSearchParams({q:searchQuery});if(scope.applied.start)params.set('start',scope.applied.start);if(scope.applied.end)params.set('end',scope.applied.end);setSearchResult(await api(`/api/search?${params}`))}catch(err){setError(requestError(err))}}}><input value={searchQuery} onChange={e=>setSearchQuery(e.target.value)} placeholder="Try peak hours, voltage, kitchen use"/><button className="btn secondary"><Icon name="search" size={14}/> Search</button></form>{searchResult&&<div className="search-hits">{searchResult.results?.map((item,i)=><article key={`${item.title}-${i}`}><b>{item.title}</b><small>{item.kind} Â· relevance {item.score}</small><p>{item.text}</p></article>)}{!searchResult.results?.length&&<p>No matching passages. Try a simpler energy keyword.</p>}</div>}</details>
      <StatusMessage error>{error}</StatusMessage><p className="copilot-disclaimer">Answers use measured household data. The source has no tariffs, weather, occupancy, or verified equipment-fault labels.</p>
    </section></>;
}

function ChatMessage({message,onRate,onAsk}) {
  if(message.pending)return <div className="message assistant"><span className="bot-avatar"><Icon name="copilot" size={15}/></span><div className="message-body">{message.text}<span className="typing-dots">Workingâ€¦</span></div></div>;
  return <div className={`message ${message.role}`}><span className={message.role==='assistant'?'bot-avatar':'user-avatar'}>{message.role==='assistant'?'G':'You'}</span><div className="message-body">{message.text}{message.result&&<details><summary>Agent trace Â· {message.result.trace?.length||0} steps</summary><div className="trace-list">{message.result.trace?.map((step,i)=><div key={`${step.agent}-${i}`}><b>{step.agent}</b><span>{step.finding}</span></div>)}</div></details>}{message.result?.suggested_questions?.length>0&&<div className="suggestion-chips message-suggestions">{message.result.suggested_questions.map((prompt,i)=><button key={`${prompt}-${i}`} onClick={()=>onAsk(prompt)}>{prompt}</button>)}</div>}{message.result?.search_results?.length>0&&<details><summary>Supporting evidence Â· {message.result.search_results.length} sources</summary><div className="trace-list">{message.result.search_results.map((source,i)=><div key={`${source.title}-${i}`}><b>{source.title}</b><span>{source.text}</span></div>)}</div></details>}{message.evaluationId&&<ResponseReview id={message.evaluationId} result={message.result} onRate={onRate}/>}</div></div>;
}
function ResponseReview({id,result,onRate}) { const [rating,setRating]=useState(()=>safeRead('gridsense.chatEvaluation').find(item=>item.id===id)?.rating);function rate(value){onRate(id,value);setRating(value)}return <div className="response-review"><span>Trace: {result?.trace?.length||0} Â· evidence: {result?.search_results?.length||0}</span><div><button onClick={()=>rate('helpful')}>{rating==='helpful'?'âœ“ Helpful':'Helpful'}</button><button onClick={()=>rate('review')}>{rating==='review'?'âœ“ Needs review':'Needs review'}</button></div></div>; }

function rateStoredResponse(id,rating) { const history=safeRead('gridsense.chatEvaluation');const next=history.map(item=>item.id===id?{...item,rating,rated_at:new Date().toISOString()}:item);try{localStorage.setItem('gridsense.chatEvaluation',JSON.stringify(next))}catch{}window.dispatchEvent(new CustomEvent('gridsense-evaluation-change')); }

export function InsightsPage({ refresh }) {
  const scope=useScope();const [kind,setKind]=useState('insight');
  const {data,error,loading}=useAsync(()=>api(withRange(`/api/agents/${kind}`,scope.applied.start,scope.applied.end)),[refresh,kind,scope.applied.start,scope.applied.end]);
  return <><PageIntro eyebrow="AGENT 04 / CROSS-AGENT SYNTHESIS" title={kind==='insight'?'Cross-agent energy brief':'Evidence-based next step'} text={kind==='insight'?'Combine demand, anomaly, and forecast findings into one evidence-led brief.':'Turn measured peaks and anomaly candidates into a cautious action to review.'} action={<div className="mode-picker"><button className={kind==='insight'?'active':''} onClick={()=>setKind('insight')}>Insight brief</button><button className={kind==='decision'?'active':''} onClick={()=>setKind('decision')}>Decision support</button></div>}/><DateScope {...scope}/>{error&&<StatusMessage error>{error}</StatusMessage>}{loading&&!data?<Loading/>:data&&kind==='insight'?<><div className="metric-grid compact"><Metric label="PERIOD START" value={data.period.start.slice(0,10)} note="Included history"/><Metric label="PERIOD END" value={data.period.end.slice(0,10)} note="Included history"/><Metric label="HOURS REVIEWED" value={Number(data.period.hours).toLocaleString()} note="Hourly records"/></div><div className="finding-grid">{data.findings.map((finding,i)=><article className="finding-card" key={`${finding.agent}-${i}`}><span>{finding.agent}</span><h3>{finding.title}</h3><p>{finding.text}</p><details><summary>View evidence</summary><pre>{JSON.stringify(finding.evidence,null,2)}</pre></details></article>)}</div><StatusMessage>{data.caveat}</StatusMessage></>:data&&<><section className="decision-card"><span className="priority-pill">{data.recommendation.priority}</span><div className="eyebrow">RECOMMENDED NEXT STEP</div><h3>{data.recommendation.action}</h3><p>{data.recommendation.reason}</p><div className="evidence-box"><b>Evidence basis</b><p>{data.recommendation.basis}</p></div></section><StatusMessage>{data.caveat}</StatusMessage></>}</>;
}

export function ReportsPage({ refresh }) {
  const scope=useScope();const {data,error,loading}=useAsync(()=>api(withRange('/api/summary',scope.applied.start,scope.applied.end)),[refresh,scope.applied.start,scope.applied.end]);
  function exportCsv(){if(!data)return;const rows=[['date','mean_demand_kw','peak_demand_kw','energy_kwh'],...(data.daily||[]).map(x=>[x.date,x.mean_kw,x.peak_kw,x.energy_kwh])];const blob=new Blob([rows.map(row=>row.map(value=>'"'+String(value).replaceAll('"','""')+'"').join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='gridsense-energy-report.csv';link.click();URL.revokeObjectURL(link.href);}
  return <><PageIntro eyebrow="GRID INTELLIGENCE / EXPORTS" title="Energy reports" text="Generate a household energy summary and export daily demand measurements as CSV." action={data&&<button className="btn primary" onClick={exportCsv}><Icon name="download" size={15}/> Export daily CSV</button>}/><DateScope {...scope}/>{error&&<StatusMessage error>{error}</StatusMessage>}{loading&&!data?<Loading/>:data&&<><div className="metric-grid"><Metric label="DAILY ROWS" value={data.daily.length.toLocaleString()} note="In the selected scope"/><Metric label="AVERAGE DEMAND" value={`${data.mean_kw} kW`} note="Hourly mean"/><Metric label="PEAK DEMAND" value={`${data.max_kw} kW`} note={data.max_at.replace('T',' ').slice(0,16)} tone="indigo"/><Metric label="ENERGY IN RANGE" value={`${Number(data.total_energy_kwh).toLocaleString()} kWh`} note="Estimated household total" tone="green"/></div><Card title="Daily report preview" subtitle={`Source history: ${data.start.slice(0,10)} through ${data.end.slice(0,10)} Â· showing latest 30 days`}><DailyTable days={data.daily.slice(-30)}/></Card></>}</>;
}
function DailyTable({days}){return <div className="table-scroll"><table><thead><tr><th>DATE</th><th>AVERAGE DEMAND</th><th>PEAK DEMAND</th><th>ENERGY</th></tr></thead><tbody>{days.map(day=><tr key={day.date}><td>{day.date}</td><td>{day.mean_kw} kW</td><td>{day.peak_kw} kW</td><td>{day.energy_kwh} kWh</td></tr>)}</tbody></table></div>}

export function EvaluationPage({ refresh }) {
  const scope=useScope();
  const {data,error,loading}=useAsync(async()=>{const [evaluation,quality]=await Promise.all([api(withRange('/api/evaluation',scope.applied.start,scope.applied.end)),api('/api/data-quality')]);return {evaluation,quality};},[refresh,scope.applied.start,scope.applied.end]);
  const [chats,setChats]=useState(()=>safeRead('gridsense.chatEvaluation'));const [legacy,setLegacy]=useState(()=>legacyPrompts(chats));
  useEffect(()=>{const update=()=>{const items=safeRead('gridsense.chatEvaluation');setChats(items);setLegacy(legacyPrompts(items));};window.addEventListener('gridsense-evaluation-change',update);window.addEventListener('storage',update);return()=>{window.removeEventListener('gridsense-evaluation-change',update);window.removeEventListener('storage',update)}},[]);
  async function replay(prompt){try{const result=await api('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:prompt.q,start:scope.applied.start||null,end:scope.applied.end||null})});saveEvaluation(prompt.q,result,true);const items=safeRead('gridsense.chatEvaluation');setChats(items);setLegacy(legacyPrompts(items));}catch(err){alert(`Could not re-run question: ${requestError(err)}`)}}
  return <><PageIntro eyebrow="EVALUATION / DATA QUALITY" title="Data quality & evaluation" text="Review forecast performance, cleaned dataset readiness, and every saved Copilot response."/><DateScope {...scope}/>{error&&<StatusMessage error>{error}</StatusMessage>}{loading&&!data?<Loading/>:data&&<><Card title="Forecast model evaluation" subtitle={`${data.evaluation.model} chronological holdout Â· ${data.evaluation.note}`}><div className="metric-grid compact"><Metric label="MAE" value={`${data.evaluation.mae_kw} kW`} note="Mean absolute error"/><Metric label="RMSE" value={`${data.evaluation.rmse_kw} kW`} note="Root mean squared error" tone="indigo"/><Metric label="MAPE" value={`${data.evaluation.mape_percent}%`} note="Percentage error" tone="violet"/><Metric label="TRAIN / TEST" value={`${Number(data.evaluation.train_hours).toLocaleString()} / ${Number(data.evaluation.test_hours).toLocaleString()}`} note="Hourly observations"/></div></Card><Card title="Dataset readiness" subtitle="Live check of cleaned records loaded by the backend"><div className="metric-grid"><Metric label="STATUS" value={data.quality.status} note="Data service" tone="green"/><Metric label="RECORDS PROCESSED" value={Number(data.quality.records_processed).toLocaleString()} note="Cleaned minute records"/><Metric label="MISSING VALUES" value={Number(data.quality.missing_values_after_cleaning).toLocaleString()} note="Across meter fields"/><Metric label="VALID NUMERIC ROWS" value={Number(data.quality.valid_numeric_records).toLocaleString()} note="All meter readings present"/><Metric label="DATE COVERAGE" value={`${data.quality.date_start.slice(0,10)} â€“ ${data.quality.date_end.slice(0,10)}`} note={data.quality.sampling_frequency}/></div></Card></>}
    <ChatEvaluation chats={chats} legacy={legacy} onRate={rateStoredResponse} onReplay={replay}/>
    <StatusMessage>Chat ratings are human feedback, not ground-truth accuracy labels. Archived prompts that predate answer logging must be re-run; the new response is identified as a replay.</StatusMessage></>;
}
function legacyPrompts(chats){const prompts=safeRead('gridsense.queryHistory');return prompts.filter(item=>item.q&&!chats.some(chat=>chat.question===item.q)).filter((item,i,list)=>list.findIndex(other=>other.q===item.q)===i)}
function ChatEvaluation({chats,legacy,onRate,onReplay}) {
  const rated=chats.filter(x=>x.rating).length;const helpful=chats.filter(x=>x.rating==='helpful').length;const traceRate=chats.length?Math.round(chats.filter(x=>x.trace_count>0).length/chats.length*100):0;
  return <Card title="AI Copilot conversation evaluation" subtitle="Inspect response traces and evidence; record helpfulness for current and saved responses."><div className="metric-grid compact"><Metric label="SAVED RESPONSES" value={chats.length} note="Saved in this browser"/><Metric label="TRACE COVERAGE" value={`${traceRate}%`} note="Responses with agent traces"/><Metric label="USER REVIEWED" value={rated} note={`${chats.length-rated} awaiting feedback`}/><Metric label="MARKED HELPFUL" value={helpful} note={`Of ${rated} submitted ratings`} tone="green"/></div><div className="table-scroll"><table className="evaluation-table"><thead><tr><th>DATE</th><th>QUESTION / RESPONSE</th><th>TRACE & SOURCES</th><th>REVIEW</th></tr></thead><tbody>{chats.map(item=><tr key={item.id}><td>{new Date(item.at).toLocaleString()}</td><td><b>{item.question}</b><p className="answer-preview">{item.answer?.slice(0,240) || 'No saved response text'}{item.answer?.length>240?'...':''}</p><small>{item.mode} Â· {item.status}{item.replayed?' Â· Re-run':''}</small></td><td>{item.trace_count||0} steps Â· {item.evidence_count||0} sources<details><summary>Inspect trace</summary>{item.trace?.map((step,i)=><p key={`${step.agent}-${i}`}><b>{step.agent}</b><br/>{step.finding}</p>)}{item.sources?.map((source,i)=><p key={`${source.title}-${i}`}><b>{source.title}</b><br/>{source.text}</p>)}</details></td><td><span className={`rating-tag ${item.rating||'waiting'}`}>{item.rating==='helpful'?'Helpful':item.rating==='review'?'Needs review':'Awaiting feedback'}</span><div className="rating-actions"><button onClick={()=>onRate(item.id,'helpful')}>Helpful</button><button onClick={()=>onRate(item.id,'review')}>Needs review</button></div></td></tr>)}{legacy.map((item,i)=><tr key={`old-${item.at}-${i}`}><td>{item.at?new Date(item.at).toLocaleString():'Earlier history'}</td><td><b>{item.q}</b><p className="answer-preview">Prior response was not saved.</p><small>Archived prompt only</small></td><td>Not recorded</td><td><button className="btn table-btn" onClick={()=>onReplay(item)}>Re-run to evaluate</button></td></tr>)}</tbody></table>{!chats.length&&!legacy.length&&<EmptyState title="No Copilot history yet" text="Ask a question in AI Copilot to start a response evaluation history."/>}</div></Card>;
}

function Loading(){return <div className="loading"><span className="spinner"/>Loading real household analytics...</div>}

export default App;



