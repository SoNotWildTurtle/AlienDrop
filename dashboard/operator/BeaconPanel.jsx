// MINC - BeaconPanel.jsx (Upgraded Real-Time Beacon Grid)

import React, { useEffect, useState } from 'react';

const BeaconPanel = () => {
  const [beacons, setBeacons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchBeacons = () => {
    fetch('/output/beacons/live.json')
      .then(res => res.json())
      .then(data => {
        setBeacons(data);
        setLoading(false);
        setLastUpdated(new Date().toLocaleTimeString());
      })
      .catch(() => {
        setBeacons([]);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchBeacons();
    const interval = setInterval(fetchBeacons, 15000);
    return () => clearInterval(interval);
  }, []);

  const formatAgo = (ts) => {
    if (!ts) return "n/a";
    const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  };

  const sorted = [...beacons].sort((a, b) => {
    if (a.alive === b.alive) {
      return new Date(b.ts) - new Date(a.ts); // newest first
    }
    return a.alive ? -1 : 1;
  });

  return (
    <div className="beacon-panel">
      <h4>📡 Beacon Health Panel</h4>
      {loading && <p>Checking C2 grid...</p>}
      {!loading && (
        <>
          <div className="meta-line">
            <span><b>Live:</b> {sorted.filter(b => b.alive).length}</span>
            <span><b>Last Checked:</b> {lastUpdated}</span>
            <button onClick={fetchBeacons}>🔄</button>
          </div>
          <ul className="beacon-list">
            {sorted.map((b, i) => (
              <li key={i} className={b.alive ? 'status-live' : 'status-dead'}>
                <span className="id">{b.shell_id}</span>
                <span className="ago">{formatAgo(b.ts)}</span>
                <span className="type">{b.beacon_type || 'heartbeat'}</span>
                <span className="tags">{(b.tags || []).join(', ')}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
};

export default BeaconPanel;

