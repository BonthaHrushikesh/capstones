export function EvidencePanel({ evidence = [] }) {
  return <details className="evidence-panel"><summary>Supporting evidence ({evidence.length})</summary>
    <ul>{evidence.map((item, index) => <li key={item.title || index}><b>{item.title || 'Evidence'}</b><p>{item.text || String(item)}</p></li>)}</ul>
  </details>;
}
