import { Icon } from './index';

export function Sidebar({ nav, view, ready, expanded, onToggle, onNavigate }) {
  return <aside className={`sidebar ${expanded ? '' : 'sidebar-collapsed'}`}>
    <div className="sidebar-system"><span className={ready ? 'online-dot' : 'offline-dot'}/><span><b>System status</b><small>{ready ? 'All systems operational' : 'Checking data service'}</small></span></div>
    <div className="nav-caption">WORKSPACE</div>
    <nav aria-label="Main navigation">{nav.map(item => <button key={item.id} className={`nav-link ${view === item.id ? 'selected' : ''}`} title={item.label} onClick={() => onNavigate(item.id)}><Icon name={item.icon}/><span>{item.label}</span></button>)}</nav>
    <div className="sidebar-bottom"><span className="source-mark"><Icon name="quality" size={15}/></span><span><b>UCI household dataset</b><small>Historical readings, 2006-2010</small></span></div>
    <button className="collapse-sidebar" onClick={onToggle}>{expanded ? 'Collapse navigation' : 'Expand navigation'}</button>
  </aside>;
}
