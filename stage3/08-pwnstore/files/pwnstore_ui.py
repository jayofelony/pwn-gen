"""
PwnStore UI - Bundled Plugin Store for Pwnagotchi
Browse and install community plugins directly from the web UI.
Ships as a default plugin in wpa-2/pwnagotchi.

Author: WPA2
Version: 1.3.0
"""

import logging
import json
import subprocess
import requests
import os
import re
import _thread
from flask import request, Response

import pwnagotchi.plugins as plugins

try:
    from flask_wtf.csrf import generate_csrf
    CSRF_AVAILABLE = True
except ImportError:
    CSRF_AVAILABLE = False


class PwnStoreUI(plugins.Plugin):
    __author__ = 'WPA2'
    __version__ = '1.3.0'
    __license__ = 'GPL3'
    __description__ = 'PwnStore - community plugin manager with web UI. Browse and install plugins without SSH.'

    # Default options (overridden by config.toml)
    OPTIONS = {
        'enabled': True,
    }

    def __init__(self):
        self.ready = False
        self.store_url = "https://raw.githubusercontent.com/wpa-2/pwnagotchi-store/main/plugins.json"

    def on_loaded(self):
        # Allow config.toml to override the store URL, e.g. for private/dev registries:
        #   main.plugins.pwnstore_ui.store_url = "http://my-server/plugins.json"
        if hasattr(self, 'options') and self.options.get('store_url'):
            self.store_url = self.options['store_url']
        logging.info("[pwnstore_ui] Loaded — store: %s", self.store_url)
        self.ready = True

    def on_webhook(self, path, request):
        """Handle web requests to /plugins/pwnstore_ui/<path>"""
        if not path or path == "/":
            return Response(self._render_store(), mimetype='text/html')
        elif path == "api/plugins":
            return self._get_plugins()
        elif path == "api/installed":
            return self._get_installed()
        elif path == "api/install":
            return self._install_plugin(request)
        elif path == "api/uninstall":
            return self._uninstall_plugin(request)
        elif path == "api/configure":
            return self._configure_plugin(request)
        elif path == "api/restart":
            return self._restart_pwnagotchi()
        return Response("Not found", status=404)

    # ─────────────────────────────────────────────
    #  API handlers
    # ─────────────────────────────────────────────

    def _get_plugins(self):
        try:
            r = requests.get(self.store_url, timeout=10)
            return Response(r.text, mimetype='application/json')
        except Exception as e:
            logging.error("[pwnstore_ui] fetch registry failed: %s", e)
            return Response("[]", mimetype='application/json')

    def _get_installed(self):
        path = "/usr/local/share/pwnagotchi/custom-plugins"
        if not os.path.exists(path):
            return Response("[]", mimetype='application/json')
        files = [f.replace('.py', '') for f in os.listdir(path) if f.endswith('.py')]
        return Response(json.dumps(files), mimetype='application/json')

    def _install_plugin(self, request):
        data = request.get_json(force=True)
        name = data.get('plugin', '')
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            return Response(json.dumps({'success': False, 'error': 'invalid name'}), status=400)

        result = subprocess.run(['pwnstore', 'install', name],
                                capture_output=True, text=True)
        repo_url = ''
        try:
            plugins_list = requests.get(self.store_url, timeout=10).json()
            plugin_data = next((p for p in plugins_list if p['name'] == name), None)
            if plugin_data:
                repo_url = plugin_data.get('download_url', '')
                if '/archive/' in repo_url:
                    repo_url = repo_url.split('/archive/')[0]
        except Exception:
            pass

        return Response(json.dumps({
            'success': result.returncode == 0,
            'repo_url': repo_url,
            'output': result.stdout + result.stderr
        }), mimetype='application/json')

    def _uninstall_plugin(self, request):
        data = request.get_json(force=True)
        name = data.get('plugin', '')
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            return Response(json.dumps({'success': False, 'error': 'invalid name'}), status=400)
        result = subprocess.run(['pwnstore', 'uninstall', name],
                                capture_output=True, text=True)
        return Response(json.dumps({'success': result.returncode == 0}),
                        mimetype='application/json')

    def _configure_plugin(self, request):
        try:
            data = request.get_json(force=True)
            name = data.get('plugin')
            vals = data.get('config', {})
            if not re.match(r'^[a-zA-Z0-9_-]+$', name):
                return Response(json.dumps({'success': False, 'error': 'invalid name'}), status=400)
            config_file = "/etc/pwnagotchi/config.toml"
            with open(config_file, 'r') as f:
                lines = f.readlines()
            prefix = f"main.plugins.{name}."
            new_lines = [l for l in lines if not l.strip().startswith(prefix)]
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'
            new_lines.append(f"\n# PwnStore: {name}\n")
            new_lines.append(f"{prefix}enabled = true\n")
            for k, v in vals.items():
                if k == 'enabled':
                    continue
                v_str = str(v).strip()
                if v_str.lower() in ['true', 'false'] or v_str.isdigit() or \
                        (v_str.startswith('[') and v_str.endswith(']')):
                    new_lines.append(f"{prefix}{k} = {v_str.lower() if v_str.lower() in ['true','false'] else v_str}\n")
                else:
                    new_lines.append(f'{prefix}{k} = "{v_str}"\n')
            with open(config_file, 'w') as f:
                f.writelines(new_lines)
            return Response(json.dumps({'success': True}), mimetype='application/json')
        except Exception as e:
            return Response(json.dumps({'success': False, 'error': str(e)}), status=500)

    def _restart_pwnagotchi(self):
        def _do_restart():
            import time
            time.sleep(1)
            subprocess.run(['systemctl', 'restart', 'pwnagotchi'])
        _thread.start_new_thread(_do_restart, ())
        return Response(json.dumps({'success': True}), mimetype='application/json')

    # ─────────────────────────────────────────────
    #  Web UI
    # ─────────────────────────────────────────────

    def _render_store(self):
        csrf_token = ''
        if CSRF_AVAILABLE:
            try:
                csrf_token = generate_csrf()
            except Exception:
                pass

        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="csrf-token" content="__CSRF_TOKEN__">
    <title>PwnStore</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Courier New', monospace; background: #000; color: #0f0; padding: 10px; overflow-x: hidden; }
        .header { text-align: center; padding: 15px 10px; border-bottom: 2px solid #0f0; margin-bottom: 20px; }
        .ascii-logo { font-size: 10px; line-height: 1.2; white-space: pre; color: #0f0; margin-bottom: 10px; }
        h1 { font-size: 20px; margin: 10px 0; color: #0f0; }
        .btn-header { display: inline-block; margin: 5px; padding: 8px 16px; background: #0f0; color: #000;
                      text-decoration: none; border-radius: 3px; font-weight: bold; font-size: 12px;
                      cursor: pointer; border: none; font-family: 'Courier New', monospace; transition: all 0.2s; }
        .btn-header:hover { background: #fff; }
        .btn-restart { background: #f00; color: #fff; }
        .btn-restart:hover { background: #f88; }
        .search-bar { width: 100%; max-width: 500px; margin: 15px auto; display: block;
                      padding: 10px; background: #111; border: 2px solid #0f0; color: #0f0;
                      font-family: 'Courier New', monospace; font-size: 14px; }
        .filters { text-align: center; margin: 10px 0; display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }
        .filter-btn { padding: 6px 14px; background: #111; border: 2px solid #0f0; color: #0f0; cursor: pointer;
                      font-family: 'Courier New', monospace; font-size: 12px; transition: all 0.2s; }
        .filter-btn:hover, .filter-btn.active { background: #0f0; color: #000; }
        .stats { text-align: center; margin: 10px 0; font-size: 12px; }
        .plugins-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; padding: 10px; }
        @media (max-width: 600px) { .plugins-grid { grid-template-columns: 1fr; } }
        .plugin-card { background: #111; border: 2px solid #0f0; padding: 15px; transition: all 0.2s; position: relative; }
        .plugin-card:hover { border-color: #fff; box-shadow: 0 0 12px #0f0; }
        .plugin-name { font-size: 15px; font-weight: bold; color: #0f0; margin-bottom: 4px; }
        .plugin-author { font-size: 11px; color: #0a0; margin-bottom: 6px; }
        .plugin-desc { font-size: 12px; color: #0f0; line-height: 1.4; margin-bottom: 10px; }
        .plugin-version { font-size: 10px; color: #060; }
        .plugin-category { font-size: 10px; padding: 2px 6px; background: #0f0; color: #000;
                           border-radius: 2px; display: inline-block; margin-bottom: 8px; }
        .status-badge { position: absolute; top: 8px; right: 8px; font-size: 10px; padding: 2px 6px;
                        border-radius: 2px; font-weight: bold; }
        .installed { background: #0f0; color: #000; }
        .plugin-actions { display: flex; gap: 8px; }
        .btn { flex: 1; padding: 7px; border: 1px solid #0f0; background: #000; color: #0f0; cursor: pointer;
               font-family: 'Courier New', monospace; font-size: 11px; transition: all 0.2s; }
        .btn:hover { background: #0f0; color: #000; }
        .btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .btn-remove { border-color: #f00; color: #f00; }
        .btn-remove:hover { background: #f00; color: #000; }
        .btn-sm { flex: 0 0 auto; padding: 7px 10px; }
        .toast { position: fixed; bottom: 20px; right: 20px; padding: 12px 18px; border: 2px solid #0f0;
                 background: #000; color: #0f0; font-size: 12px; z-index: 9000; max-width: 300px;
                 animation: fadeIn 0.3s; }
        .toast.err { border-color: #f00; color: #f00; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .loading { text-align: center; padding: 40px; }
        .footer { text-align: center; padding: 20px; margin-top: 20px; border-top: 2px solid #0f0; font-size: 11px; }
        .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.9); display: flex;
                         align-items: center; justify-content: center; z-index: 8000; padding: 20px; }
        .modal { background: #000; border: 2px solid #0f0; padding: 25px; max-width: 460px;
                 width: 100%; box-shadow: 0 0 25px #0f0; }
        .modal h2 { font-size: 18px; text-align: center; margin-bottom: 15px; }
        .modal p { font-size: 13px; text-align: center; margin-bottom: 15px; }
        .modal-btn { display: block; width: 100%; padding: 10px; border: 2px solid #0f0;
                     background: #000; color: #0f0; cursor: pointer; font-family: 'Courier New', monospace;
                     font-size: 13px; margin-top: 8px; text-decoration: none; text-align: center; }
        .modal-btn:hover { background: #0f0; color: #000; }
        .modal-btn.dim { border-color: #444; color: #666; }
    </style>
</head>
<body>
<div class="header">
    <div class="ascii-logo">(◕‿‿◕)</div>
    <h1>🛒 PwnStore</h1>
    <p style="font-size:12px; margin-bottom:10px;">Community Plugin Manager</p>
    <a href="https://buymeacoffee.com/wpa2" target="_blank" class="btn-header">☕ Support Dev</a>
    <button class="btn-header btn-restart" onclick="restartService()">🔄 Restart</button>
</div>

<input id="searchBox" type="text" class="search-bar" placeholder="🔍 Search plugins...">

<div class="filters">
    <button class="filter-btn active" data-cat="all">All</button>
    <button class="filter-btn" data-cat="Display">Display</button>
    <button class="filter-btn" data-cat="GPS">GPS</button>
    <button class="filter-btn" data-cat="Attack">Attack</button>
    <button class="filter-btn" data-cat="System">System</button>
    <button class="filter-btn" data-cat="Notification">Notify</button>
    <button class="filter-btn" data-cat="Backup">Backup</button>
</div>

<div class="stats" id="statsLine">Loading...</div>
<div id="grid" class="plugins-grid"><div class="loading">Fetching plugin registry...</div></div>

<div class="footer">
    PwnStore v1.3.0 · Built by <strong>WPA2</strong> ·
    <a href="https://github.com/wpa-2/pwnagotchi-store" style="color:#0f0">GitHub</a>
</div>

<script>
let all = [], installed = [], cat = 'all', search = '';

function csrf() {
    const m = document.querySelector('meta[name="csrf-token"]');
    return m ? m.content : '';
}

async function api(url, opts = {}) {
    const h = { 'Content-Type': 'application/json', ...opts.headers };
    if (opts.method === 'POST') { const t = csrf(); if (t) h['X-CSRFToken'] = t; }
    const r = await fetch(url, { ...opts, headers: h });
    return r.json();
}

async function load() {
    try {
        [all, installed] = await Promise.all([
            api('/plugins/pwnstore_ui/api/plugins'),
            api('/plugins/pwnstore_ui/api/installed')
        ]);
        render();
    } catch(e) { toast('Failed to load plugin registry', true); }
}

function render() {
    let list = all.filter(p => {
        const matchCat = cat === 'all' || p.category === cat;
        const matchQ = !search || p.name.toLowerCase().includes(search) || (p.description||'').toLowerCase().includes(search);
        return matchCat && matchQ;
    });
    document.getElementById('statsLine').textContent = `${list.length} plugin${list.length!==1?'s':''} shown`;
    document.getElementById('grid').innerHTML = list.length
        ? list.map(card).join('')
        : '<div class="loading" style="color:#f80">No plugins match your filter.</div>';
}

function card(p) {
    const inst = installed.includes(p.name);
    return `<div class="plugin-card">
        ${inst ? '<span class="status-badge installed">✓ INSTALLED</span>' : ''}
        <div class="plugin-name">${p.name}</div>
        <div class="plugin-author">by ${p.author || 'Unknown'}</div>
        ${p.category ? `<span class="plugin-category">${p.category}</span>` : ''}
        <div class="plugin-desc">${p.description || ''}</div>
        <div class="plugin-version">v${p.version || '?'}</div>
        <div class="plugin-actions" style="margin-top:10px">
            ${inst
                ? `<button class="btn btn-remove" onclick="remove('${p.name}')">Uninstall</button>`
                : `<button class="btn" onclick="install('${p.name}')">Install</button>`
            }
            <button class="btn btn-sm" onclick="info('${p.name}')">ℹ️</button>
        </div>
    </div>`;
}

async function install(name) {
    toast(`Installing ${name}…`);
    const res = await api('/plugins/pwnstore_ui/api/install', {
        method: 'POST', body: JSON.stringify({plugin: name})
    });
    if (res.success) {
        installed.push(name);
        render();
        showModal(name, res.repo_url);
    } else {
        toast(`Install failed: ${res.output || ''}`, true);
    }
}

async function remove(name) {
    if (!confirm(`Remove ${name}?`)) return;
    const res = await api('/plugins/pwnstore_ui/api/uninstall', {
        method: 'POST', body: JSON.stringify({plugin: name})
    });
    if (res.success) {
        installed = installed.filter(x => x !== name);
        render(); toast(`${name} removed`);
    } else { toast('Uninstall failed', true); }
}

function info(name) {
    const p = all.find(x => x.name === name);
    if (!p) return;
    const url = (p.download_url||'').includes('/archive/') ? p.download_url.split('/archive/')[0] : p.download_url;
    showInfoModal(p, url);
}

function showModal(name, repoUrl) {
    const o = document.createElement('div');
    o.className = 'modal-overlay';
    o.innerHTML = `<div class="modal">
        <h2>✅ ${name} installed!</h2>
        <p>Configuration may be required. Edit <code>/etc/pwnagotchi/config.toml</code> then restart.</p>
        ${repoUrl ? `<a href="${repoUrl}" target="_blank" class="modal-btn">📖 Setup Instructions</a>` : ''}
        <button class="modal-btn" onclick="restartService()">🔄 Restart Now</button>
        <button class="modal-btn dim" onclick="this.closest('.modal-overlay').remove()">Close</button>
    </div>`;
    document.body.appendChild(o);
}

function showInfoModal(p, url) {
    const o = document.createElement('div');
    o.className = 'modal-overlay';
    o.innerHTML = `<div class="modal">
        <h2>${p.name} <small style="font-size:12px">v${p.version||'?'}</small></h2>
        <p style="text-align:left;margin:10px 0">${p.description||''}</p>
        <p><strong>Author:</strong> ${p.author||'?'}</p>
        ${url ? `<a href="${url}" target="_blank" class="modal-btn" style="margin-top:15px">🔗 Repository</a>` : ''}
        <button class="modal-btn dim" onclick="this.closest('.modal-overlay').remove()">Close</button>
    </div>`;
    document.body.appendChild(o);
}

async function restartService() {
    if (!confirm('Restart pwnagotchi service?')) return;
    toast('Restarting…');
    await api('/plugins/pwnstore_ui/api/restart', { method: 'POST' });
    setTimeout(() => location.reload(), 6000);
}

function toast(msg, err = false) {
    const el = document.createElement('div');
    el.className = 'toast' + (err ? ' err' : '');
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 4000);
}

document.getElementById('searchBox').oninput = e => { search = e.target.value.toLowerCase(); render(); };
document.querySelectorAll('.filter-btn').forEach(b => {
    b.onclick = () => {
        document.querySelectorAll('.filter-btn').forEach(x => x.classList.remove('active'));
        b.classList.add('active');
        cat = b.dataset.cat;
        render();
    };
});

load();
</script>
</body>
</html>"""
        return html.replace('__CSRF_TOKEN__', csrf_token)
