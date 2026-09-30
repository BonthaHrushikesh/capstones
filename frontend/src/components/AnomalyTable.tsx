export function AnomalyTable({ flags = [] }) {
  return <div className="table-scroll"><table><thead><tr><th>TIME</th><th>OBSERVED</th><th>BASELINE</th><th>SCORE</th></tr></thead><tbody>
    {flags.map((row) => <tr key={row.timestamp}><td>{row.timestamp}</td><td>{row.observed_kw} kW</td><td>{row.baseline_kw} kW</td><td>{row.score}</td></tr>)}
  </tbody></table></div>;
}
