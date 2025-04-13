// MINC - ShellDetails.jsx (Upgraded Tactical Shell View)

import React from 'react';
import './styles.css';

const ShellDetails = ({ shell, onTransfer, onClose }) => {
  const {
    shell_id,
    target,
    platform,
    tags = [],
    modules = [],
    beacon_alive,
    tasks = [],
    recon_fingerprint = {},
    timestamp,
    last_seen,
    kill_flag,
    memory_flag
  } = shell;

  const printReconSummary = () => {
    const { platform, cms, open_ports = [], paths = [] } = recon_fingerprint;
    return (
      <>
        <strong>Platform:</strong> {platform || 'n/a'} <br />
        <strong>CMS:</strong> {cms || 'unknown'} <br />
        <strong>Open Ports:</strong> {open_ports.join(', ') || 'n/a'} <br />
        <strong>Paths:</strong> {paths.join(', ') || 'n/a'}
      </>
    );
  };

  return (
    <div className="shell-details">
      <div className="detail-header">
        <h3>🧬 Shell: {shell_id}</h3>
        <button className="close-btn" onClick={onClose}>✖ Close</button>
      </div>

      <div className="detail-section">
        <strong>🎯 Target:</strong> {target} <br />
        <strong>🖥 Platform:</strong> {platform} <br />
        <strong>📡 Status:</strong>{' '}
        {beacon_alive ? (
          <span className="status-live">🟢 Online</span>
        ) : (
          <span className="status-dead">🔴 Silent</span>
        )} <br />
        <strong>🕒 First Seen:</strong> {timestamp || 'unknown'} <br />
        <strong>⏳ Last Seen:</strong> {last_seen || 'unknown'} <br />
        <strong>🏷 Tags:</strong> {tags.map((t, i) => <span key={i} className={`tag tag-${t}`}>{t}</span>)}{' '}
        {memory_flag && <span title="Memory-only" className="flag-icon">🧠</span>}
        {kill_flag && <span title="Killmode active" className="flag-icon danger">☠️</span>}
      </div>

      <div className="detail-section">
        <h4>🧠 Recon Summary</h4>
        {printReconSummary()}
        <details style={{ marginTop: '8px' }}>
          <summary>📦 Raw Recon JSON</summary>
          <pre>{JSON.stringify(recon_fingerprint, null, 2)}</pre>
        </details>
      </div>

      <div className="detail-section">
        <h4>⚙️ Modules</h4>
        {modules.length > 0 ? (
          <ul>
            {modules.map((m, i) => <li key={i}>{m}</li>)}
          </ul>
        ) : <span>None reported</span>}
      </div>

      <div className="detail-section">
        <h4>📝 Task Queue</h4>
        {tasks.length > 0 ? (
          <ul>
            {tasks.map((task, i) => <li key={i}>🔸 {task}</li>)}
          </ul>
        ) : <span>No tasks queued</span>}
        <button className="cli-btn" onClick={() => alert('Launching TaskCLI...')}>💻 Open CLI</button>
      </div>

      <div className="detail-actions">
        <button onClick={onTransfer}>🚚 Transfer</button>
        <button onClick={() => alert('Tag Editor Coming Soon')}>🏷 Edit Tags</button>
        <button className="danger-btn" onClick={() => alert('⚠️ Kill command issued.')}>☠️ Kill</button>
      </div>
    </div>
  );
};

export default ShellDetails;

