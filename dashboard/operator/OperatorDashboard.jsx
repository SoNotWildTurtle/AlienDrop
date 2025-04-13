// MINC - OperatorDashboard.jsx (Upgraded Dashboard)

import React, { useState, useEffect } from 'react';
import ShellGrid from './ShellGrid.jsx';
import ShellDetails from './ShellDetails.jsx';
import TransferWizard from './TransferWizard.jsx';
import BeaconPanel from './BeaconPanel.jsx';
import './styles.css';

const OperatorDashboard = () => {
  const [shells, setShells] = useState([]);
  const [selectedShell, setSelectedShell] = useState(null);
  const [filter, setFilter] = useState('');
  const [transferMode, setTransferMode] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  // === POLL DATA ===
  const fetchShells = () => {
    fetch('/output/shells/shells.json')
      .then(res => res.json())
      .then(data => {
        setShells(data);
        setLastUpdated(new Date().toLocaleTimeString());
      })
      .catch(() => setShells([]));
  };

  useEffect(() => {
    fetchShells();
    const interval = setInterval(fetchShells, 10000); // refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const handleShellSelect = (shell) => {
    setSelectedShell(shell);
    setTransferMode(false);
  };

  const handleTagFilter = (tag) => {
    setFilter(tag === filter ? '' : tag); // toggle tag
  };

  const filteredShells = filter
    ? shells.filter(s => (s.tags || []).includes(filter))
    : shells;

  const tagSet = Array.from(
    new Set(shells.flatMap(s => s.tags || []))
  );

  return (
    <div className="dashboard-container">
      <h1>AlienDrop Operator Dashboard</h1>
      <div className="dashboard-meta">
        <BeaconPanel />
        <div className="meta-line">
          <span><b>Total Shells:</b> {shells.length}</span>
          <span><b>Visible:</b> {filteredShells.length}</span>
          <span><b>Last Sync:</b> {lastUpdated || 'n/a'}</span>
          <button onClick={fetchShells}>🔄 Refresh</button>
        </div>
        <div className="tag-filters">
          <span><b>Tags:</b></span>
          {tagSet.map(tag => (
            <button
              key={tag}
              className={filter === tag ? 'active' : ''}
              onClick={() => handleTagFilter(tag)}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      <div className="dashboard-main">
        <ShellGrid shells={filteredShells} onSelect={handleShellSelect} />

        {selectedShell && !transferMode && (
          <ShellDetails
            shell={selectedShell}
            onTransfer={() => setTransferMode(true)}
            onClose={() => setSelectedShell(null)}
          />
        )}

        {transferMode && (
          <TransferWizard
            shell={selectedShell}
            onClose={() => setTransferMode(false)}
          />
        )}
      </div>
    </div>
  );
};

export default OperatorDashboard;
