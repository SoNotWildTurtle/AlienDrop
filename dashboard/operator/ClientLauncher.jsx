<!-- MINC - client_launcher.html -->
<!DOCTYPE html>
<html>
<head>
  <title>AlienDrop Client Launcher</title>
  <meta charset="UTF-8" />
  <style>
    body { background: #111; color: #eee; font-family: monospace; padding: 2em; }
    h2 { margin-bottom: 1em; }
    .dash-list { margin-top: 2em; }
    .dash-entry { margin-bottom: 0.5em; border-bottom: 1px solid #333; padding-bottom: 0.5em; }
    .preview { margin-top: 1em; background: #1c1c1c; padding: 1em; }
    iframe { width: 100%; height: 400px; border: 1px solid #555; }
  </style>
</head>
<body>

<h2>🛰 AlienDrop Client Launcher</h2>
<p>Select one or more `client_dashboard_*.html` files to preview and access:</p>

<input type="file" id="loader" multiple accept=".html" />
<div id="dashList" class="dash-list"></div>

<script>
  const loader = document.getElementById('loader');
  const dashList = document.getElementById('dashList');

  loader.addEventListener('change', () => {
    dashList.innerHTML = '';
    [...loader.files].forEach(file => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const entry = document.createElement('div');
        entry.className = 'dash-entry';
        entry.innerHTML = `
          <strong>${file.name}</strong><br/>
          <button onclick="openPreview('${file.name}')">📂 Open</button>
          <div class="preview" id="prev_${file.name.replace(/\W/g, '_')}"></div>
        `;
        dashList.appendChild(entry);

        const blobUrl = URL.createObjectURL(file);
        const previewDiv = entry.querySelector('.preview');
        previewDiv.innerHTML = `<iframe src="${blobUrl}"></iframe>`;
      };
      reader.readAsText(file);
    });
  });
</script>

</body>
</html>

