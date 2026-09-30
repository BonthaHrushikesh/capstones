export async function api(path, options = {}) {
  const response = await fetch(path, options);
  let data;
  try { data = await response.json(); } catch { data = { detail: response.statusText }; }
  if (!response.ok) throw new Error(data.detail || response.statusText || 'Request failed');
  return data;
}

export function withRange(path, start, end) {
  const params = new URLSearchParams();
  if (start) params.set('start', start);
  if (end) params.set('end', end);
  return `${path}${params.size ? `?${params}` : ''}`;
}

export const safeRead = (key, fallback = []) => {
  try { return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback)); }
  catch { return fallback; }
};

export function saveEvaluation(question, result, replayed = false) {
  const trace = result.trace || [];
  const sources = (result.search_results || []).slice(0, 8).map((item) => ({
    title: item.title || '', kind: item.kind || '', text: String(item.text || '').slice(0, 500),
  }));
  const entry = {
    id: result.trace_id || `chat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    at: new Date().toISOString(), question, answer: result.answer || '',
    status: result.status || 'answered', trace, trace_count: trace.length,
    evidence_count: result.search_results?.length ?? 0, sources,
    mode: result.llm?.used ? 'LLM phrasing + grounded evidence' : (result.llm?.provider || 'Local grounded response'),
    confidence: result.nlp?.confidence ?? null, rating: null, replayed,
  };
  const history = safeRead('gridsense.chatEvaluation');
  try { localStorage.setItem('gridsense.chatEvaluation', JSON.stringify([entry, ...history].slice(0, 100))); } catch { /* Keep the current response available even if browser storage is full. */ }
  return entry;
}
