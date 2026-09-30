const STEPS = [
  { label: '01 / UNDERSTAND', title: 'Classify the question', text: 'Identify the requested demand metric, sub-meter, anomaly check, forecast, or method explanation.' },
  { label: '02 / SCOPE', title: 'Apply data limits', text: 'Use the selected date range and explain when billing, live-grid, or appliance-level evidence is unavailable.' },
  { label: '03 / ANALYZE', title: 'Collect requested evidence', text: 'Run only the relevant household summary, anomaly screen, forecast, or knowledge retrieval.' },
  { label: '04 / ANSWER', title: 'Write a grounded response', text: 'Answer from computed values, preserve units and caveats, then attach the agent trace and supporting evidence.' },
];

export function AgentWorkflow() {
  return <section className="architecture-card copilot-workflow" aria-label="How the Copilot builds answers">
    <div className="architecture-heading"><div><div className="eyebrow">ANSWER PIPELINE</div><h3>How Copilot builds an answer</h3><p>Every response is tied to the selected household-data scope.</p></div><span className="architecture-label">LOCAL DATA FIRST</span></div>
    <div className="architecture-flow">
      {STEPS.map((step, index) => <div className="workflow-step-wrap" key={step.label}>
        <article className={`workflow-node${index === STEPS.length - 1 ? ' workflow-final' : ''}`}><span>{step.label.slice(0, 2)}</span><div><small>{step.label.slice(5)}</small><b>{step.title}</b><p>{step.text}</p></div></article>
        {index < STEPS.length - 1 && <i className="flow-arrow" aria-hidden="true"/>}
      </div>)}
    </div>
    <p className="architecture-note">The optional language model can rephrase computed answers; it cannot add new measurements or establish physical causes.</p>
  </section>;
}

export { AgentWorkflow as WorkflowDiagram };
export default AgentWorkflow;
