// MINC - ShellGrid.jsx (Upgraded Operator Shell Grid)

import React from 'react';
import './styles.css';

const ShellGrid = ({ shells, onSelect }) => {
  return (
    <div className="shell-grid">
      <h2>🧠 Active Shells</h2>
      <table className="shell-table">
        <thead>
          <tr>
            <th>Shell ID</th>
            <th>Target</th>
            <th>Platform</th>
            <th>Tags</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {shells.map((shell) => {
            const isAlive = shell.beacon_alive;
            const tagList = shell.tags || [];
            const timestamp = shell.last_seen || shell.timestamp || "unknown";

            const memoryOnly = tagList.includes("memory") || shell.memory_flag;
            const killMode = tagList.includes("killmode") || shell.kill_flag;

            return (
              <tr
                key={shell.shell_id}
                onClick={() => onSelect(shell)}
                className={`shell-row ${isAlive ? 'alive' : 'dead'}`}
                title={`Last seen: ${timestamp}`}
              >
                <td>{shell.shell_id}</td>
                <td>{shell.target}</td>
                <td>
                  <span className={`platform-icon platform-${shell.platform}`}>
                    {shell.platform === "windows" ? "🪟" :
                     shell.platform === "linux" ? "🐧" :
                     shell.platform === "darwin" ? "🍎" : "❔"}
                  </span>
                </td>
                <td>
                  {tagList.map((tag, i) => (
                    <span key={i} className={`tag tag-${tag}`}>
                      {tag}
                    </span>
                  ))}
                  {memoryOnly && <span className="flag-icon" title="Memory-only shell">🧠</span>}
                  {killMode && <span className="flag-icon danger" title="Killmode enabled">☠️</span>}
                </td>
                <td>
                  {isAlive ? (
                    <span className="status-live" title="Beacon Active">🟢 Online</span>
                  ) : (
                    <span className="status-dead" title="No recent beacon">🔴 Silent</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default ShellGrid;

