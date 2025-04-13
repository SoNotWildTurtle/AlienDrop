// MINC - ClientBuilder.jsx (Advanced Secure Client Dashboard Builder)

import React, { useState } from 'react';

const ClientBuilder = () => {
  const [shellId, setShellId] = useState('');
  const [clientId, setClientId] = useState('');
  const [transferData, setTransferData] = useState(null);
  const [status, setStatus] = useState('');

  const loadTransfer = async () => {
    if (!shellId) return;
    try {
      const res = await fetch(`/output/transfers/transfer_${shellId}.pkg`);
      const json = await res.json();
      setTransferData(json);
      setClientId(json.client_id || '');
      setStatus('Transfer file loaded.');
    } catch (e) {
      setStatus('⚠️ Failed to load transfer file.');
    }
  };

  const buildClientPage = () => {
    if (!shellId || !clientId) {
      return setStatus('⚠️ Shell ID and Client ID required.');
    }

    const meta = transferData || {
      shell_id: shellId,
      client_id: clientId,
      transfer_date: new Date().toISOString(),
      tags: ['client'],
      modules: [],
      recon: {}
    };

    const html = `
<!DOCTYPE html>
<html>
<head>
  <title>${meta.client_id} - Shell Interface</title>
  <meta charset="UTF-8" />
  <style>
    body { background: #111; color: #eee; font-family: monospace; padding: 2em; }
    .box { border: 1px solid #555; padding: 1em; margin-top: 2em; background: #1a1a1a; }
    h2 { margin-bottom: 0.5em; }
    pre { background: #222; padding: 1em; overflow-x: auto; }
  </style>
</head>
<body>
  <h2>Secure Shell Access Panel</h2>
  <div class="box">
    <p><strong>Shell ID:</strong> ${meta.shell_id}</p>
    <p><strong>Client ID:</strong> ${meta.client_id}</p>
    <p><strong>Transfer Date:</strong> ${meta.transfer_date}</p>
    <p><strong>Tags:</strong> ${(meta.tags || []).join(', ')}</p>
    <p><strong>Modules:</strong> ${(meta.modules || []).join(', ')}</p>
    <p><strong>Recon:</strong></p>
    <pre>${JSON.stringify(meta.recon, null, 2)}</pre>
    <p>Please use the CLI interface provided separately to communicate with your node. Contact the operator if additional access is required.</p>
  </div>
</body>
</html>
    `.trim();

    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `client_dashboard_${shellId}.html`;
    link.click();

    setStatus('✅ Client page generated.');
  };

  return (
    <div className="client-builder">
      <h3>🛠 Client Dashboard Generator</h3>

      <label>Shell ID</label>
      <input
        value={shellId}
        onChange={(e) => setShellId(e.target.value)}
        placeholder="shell ID"
      />

      <label>Client ID</label>
      <input
        value={clientId}
        onChange={(e) => setClientId(e.target.value)}
        placeholder="client123"
      />

      <div style={{ marginTop: '10px' }}>
        <button onClick={loadTransfer}>🔍 Load Transfer</button>
        <button onClick={buildClientPage}>🚀 Generate Client Page</button>
      </div>

      {status && <p className="status">{status}</p>}
    </div>
  );
};

export default ClientBuilder;

