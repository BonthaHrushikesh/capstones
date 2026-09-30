import { useState } from 'react';
import { Icon } from './index';

export function Header({ title, subtitle, ready, onRefresh, onNavigate }) {
  const [profileOpen, setProfileOpen] = useState(false);
  return <header className="top-header">
    <button className="brand" onClick={() => onNavigate('overview')} aria-label="GridSense AI overview"><span className="brand-mark"><Icon name="copilot" size={18}/></span><span><b>GridSense <i>AI</i></b><small>ENERGY INTELLIGENCE</small></span></button>
    <div className="header-context"><h1>{title}</h1><p>{subtitle}</p></div>
    <div className="header-tools"><button className="btn ghost date-button" onClick={() => onNavigate('overview')}><Icon name="calendar" size={15}/> Date range</button><button className="btn ghost" onClick={onRefresh} aria-label="Refresh page"><Icon name="refresh" size={15}/><span>Refresh</span></button><button className="icon-button notification-button" onClick={() => onNavigate('anomaly')} aria-label="Open anomaly review"><Icon name="bell"/></button><div className="profile-wrap"><button className="profile-button" onClick={() => setProfileOpen(value => !value)}><span className="avatar">G</span><span className="profile-name">Energy user</span><Icon name="chevron" size={14}/></button>{profileOpen && <div className="profile-menu"><b>GridSense AI</b><small>Household data workspace</small><span className={ready ? 'online-dot' : 'offline-dot'}>{ready ? 'Data service ready' : 'Data service unavailable'}</span></div>}</div></div>
  </header>;
}
