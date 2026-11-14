// app/static/js/app.js — Core state management and API orchestration for RESQ

const state = {
  city: null,
  lastSearch: null,
  lastOptimise: null,
  lastBenchmark: null,
  comparisonResults: [],
};

const ALGO_METADATA = {
  astar:               { label: 'A* Search',                    guarantee: 'Optimal Cost Guaranteed',       badgeClass: 'pill-opt' },
  ida_star:            { label: 'IDA* Search',                  guarantee: 'Optimal Cost Guaranteed',       badgeClass: 'pill-opt' },
  bfs:                 { label: 'Breadth-First Search (BFS)',    guarantee: 'Fewest Edge Hops',              badgeClass: 'pill-few' },
  iddfs:               { label: 'Iterative Deepening DFS',      guarantee: 'Fewest Edge Hops',              badgeClass: 'pill-few' },
  greedy:              { label: 'Greedy Best-First Search',     guarantee: 'Heuristic Only (Not Optimal)',  badgeClass: 'pill-none' },
  dfs:                 { label: 'Depth-First Search (DFS)',      guarantee: 'Uninformed (Not Optimal)',      badgeClass: 'pill-none' },
  simulated_annealing: { label: 'Simulated Annealing',          guarantee: 'Stochastic Global Optimization',badgeClass: 'pill-opt' },
  random_restart:      { label: 'Random-Restart Hill Climbing', guarantee: 'Multi-Basin Exploration',       badgeClass: 'pill-opt' },
  hill_climbing:       { label: 'Steepest Hill Climbing',       guarantee: 'Local Optimum Trapping',        badgeClass: 'pill-few' },
  random_walk:         { label: 'Random Walk (Baseline)',       guarantee: 'Stochastic Baseline',           badgeClass: 'pill-none' },
};

function refreshIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// ── Notification Banner ────────────────────────────────────────────
function showBanner(msg, type = 'info') {
  const b = document.getElementById('status-banner');
  if (!b) return;
  b.textContent = msg;
  b.className = `show ${type}`;
  setTimeout(() => { b.className = ''; }, 4500);
}

function showError(msg) { showBanner(msg, 'error'); }
function showSuccess(msg) { showBanner(msg, 'success'); }
function showInfo(msg) { showBanner(msg, 'info'); }

function setLoading(btnId, loading, label = 'Processing…') {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  if (loading) {
    btn.dataset.originalHtml = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> ${label}`;
  } else {
    if (btn.dataset.originalHtml) btn.innerHTML = btn.dataset.originalHtml;
    refreshIcons();
  }
}

async function apiFetch(url, options = {}) {
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await resp.json().catch(() => ({ status: 'error', message: 'Malformed server response.' }));
  return { ok: resp.ok, status: resp.status, data };
}

function formatRoute(route) {
  if (!route || route.length === 0) return '—';
  return route.join(' → ');
}

function fmtNum(v, decimals = 3) {
  if (v == null || v === undefined) return '—';
  if (typeof v === 'number') return v.toFixed(decimals);
  return String(v);
}

function statusPill(status) {
  if (status === 'success') {
    return `<span class="pill pill-success"><i data-lucide="check"></i> Optimal Success</span>`;
  }
  if (status === 'no_route') {
    return `<span class="pill pill-danger"><i data-lucide="x"></i> No Path Available</span>`;
  }
  if (status === 'no_valid_tour') {
    return `<span class="pill pill-danger"><i data-lucide="x"></i> Infeasible Tour</span>`;
  }
  return `<span class="pill pill-warning">${status}</span>`;
}

// ── City Graph Loading & Population ────────────────────────────────
async function loadCity() {
  try {
    const { ok, data } = await apiFetch('/api/city');
    if (!ok) {
      showError(data.message || 'Failed to initialize network topology.');
      return;
    }
    state.city = data;
    renderGraph(data);
    populateDropdowns(data);
    updateOverviewStats(data);
    updateRoadInventoryTable(data);
    refreshIcons();
  } catch (e) {
    showError('Unable to connect to Flask server.');
    console.error(e);
  }
}

function populateDropdowns(city) {
  const selectElements = ['sel-start', 'sel-destination', 'sel-base', 'road-source', 'road-target'];
  for (const id of selectElements) {
    const sel = document.getElementById(id);
    if (!sel) continue;
    const current = sel.value;
    sel.innerHTML = '';
    for (const n of city.nodes) {
      const opt = document.createElement('option');
      opt.value = n.id;
      opt.textContent = `${n.id} — ${n.label}`;
      sel.appendChild(opt);
    }
    if (current && city.nodes.some(n => n.id === current)) {
      sel.value = current;
    } else if (id === 'sel-destination' && city.nodes.length > 1) {
      sel.value = city.nodes[city.nodes.length - 1].id;
    } else if (id === 'road-target' && city.nodes.length > 1) {
      sel.value = city.nodes[1].id;
    }
  }

  populateLocationCheckboxes(city);
}

function populateLocationCheckboxes(city) {
  const container = document.getElementById('opt-locations');
  if (!container) return;
  const baseNode = document.getElementById('sel-base')?.value || 'A';
  container.innerHTML = '';

  for (const n of city.nodes) {
    const label = document.createElement('label');
    label.className = 'check-item';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.value = n.id;
    cb.id = `loc-cb-${n.id}`;

    if (n.id === baseNode) {
      cb.disabled = true;
      cb.checked = false;
      label.style.opacity = '0.4';
    } else if (['C', 'D', 'H'].includes(n.id)) {
      cb.checked = true;
    }

    label.appendChild(cb);
    label.appendChild(document.createTextNode(` ${n.id} — ${n.label}`));
    container.appendChild(label);
  }
}

function getSelectedLocations() {
  const cbs = document.querySelectorAll('#opt-locations input[type="checkbox"]:checked:not(:disabled)');
  return Array.from(cbs).map(cb => cb.value);
}

function updateOverviewStats(city) {
  const statNodes   = document.getElementById('stat-nodes');
  const statRoads   = document.getElementById('stat-roads');
  const statOpen    = document.getElementById('stat-open');
  const statBlocked = document.getElementById('stat-blocked');
  const statVersion = document.getElementById('stat-version');

  if (statNodes)   statNodes.textContent = city.nodes.length;
  if (statRoads)   statRoads.textContent = city.edges.length;
  const blockedCount = city.edges.filter(e => e.blocked).length;
  if (statOpen)    statOpen.textContent = city.edges.length - blockedCount;
  if (statBlocked) statBlocked.textContent = blockedCount;
  if (statVersion) statVersion.textContent = `v${city.version}`;
}

function updateRoadInventoryTable(city) {
  const tbody = document.getElementById('roads-tbody');
  if (!tbody) return;

  tbody.innerHTML = '';
  const edges = [...city.edges].sort((a, b) => a.id.localeCompare(b.id));

  for (const edge of edges) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="font-family:var(--font-mono);font-weight:600">${edge.source} ↔ ${edge.target}</td>
      <td>${edge.weight}</td>
      <td>
        ${edge.blocked
          ? '<span class="pill pill-danger">Closed</span>'
          : '<span class="pill pill-success">Open</span>'}
      </td>
      <td>
        <button type="button" class="btn btn-outline btn-sm" style="height:24px;padding:0 8px;font-size:11px"
          onclick="toggleRoad('${edge.source}', '${edge.target}', ${edge.blocked})">
          ${edge.blocked ? 'Reopen' : 'Block'}
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  }
  refreshIcons();
}

// ── Road Controls ──────────────────────────────────────────────────
async function toggleRoad(source, target, isBlocked) {
  if (isBlocked) {
    await sendReopen(source, target);
  } else {
    await sendBlock(source, target);
  }
}

async function sendBlock(source, target) {
  try {
    const { ok, data } = await apiFetch('/api/roads/block', {
      method: 'POST',
      body: JSON.stringify({ source, target }),
    });
    if (!ok) { showError(data.message || 'Block failed.'); return; }
    onCityUpdated(data);
    showSuccess(`Road segment ${source}–${target} marked as BLOCKED.`);
  } catch (e) { showError('Network transmission failed.'); }
}

async function sendReopen(source, target) {
  try {
    const { ok, data } = await apiFetch('/api/roads/reopen', {
      method: 'POST',
      body: JSON.stringify({ source, target }),
    });
    if (!ok) { showError(data.message || 'Reopen failed.'); return; }
    onCityUpdated(data);
    showSuccess(`Road segment ${source}–${target} restored to OPEN.`);
  } catch (e) { showError('Network transmission failed.'); }
}

async function blockRoad() {
  const src = document.getElementById('road-source')?.value;
  const tgt = document.getElementById('road-target')?.value;
  if (!src || !tgt || src === tgt) {
    showError('Please choose two distinct node endpoints.');
    return;
  }
  setLoading('btn-block', true, 'Closing Road…');
  await sendBlock(src, tgt);
  setLoading('btn-block', false);
}

async function reopenRoad() {
  const src = document.getElementById('road-source')?.value;
  const tgt = document.getElementById('road-target')?.value;
  if (!src || !tgt || src === tgt) {
    showError('Please choose two distinct node endpoints.');
    return;
  }
  setLoading('btn-reopen', true, 'Opening Road…');
  await sendReopen(src, tgt);
  setLoading('btn-reopen', false);
}

async function resetScenario() {
  const btn = document.getElementById('btn-reset') || document.getElementById('btn-global-reset');
  if (btn) setLoading(btn.id, true, 'Resetting…');
  try {
    const { ok, data } = await apiFetch('/api/roads/reset', { method: 'POST', body: JSON.stringify({}) });
    if (!ok) { showError(data.message || 'Reset failed.'); return; }
    onCityUpdated(data);
    showSuccess('Network topology reset: all road segments are open.');
  } catch (e) { showError('Network transmission failed.'); }
  finally { if (btn) setLoading(btn.id, false); }
}

function onCityUpdated(cityData) {
  state.city = cityData;
  renderGraph(cityData);
  populateDropdowns(cityData);
  updateOverviewStats(cityData);
  updateRoadInventoryTable(cityData);
  clearRouteHighlight();
  clearTourHighlight();
  refreshIcons();
}

// ── Search Algorithm Routing ───────────────────────────────────────
async function runSearch() {
  const algorithm = document.getElementById('sel-algorithm')?.value || 'astar';
  const start     = document.getElementById('sel-start')?.value;
  const dest      = document.getElementById('sel-destination')?.value;
  const heuristic = document.getElementById('sel-heuristic')?.value || 'euclidean';

  if (!start || !dest) { showError('Select valid start and destination nodes.'); return; }

  setLoading('btn-search', true, 'Calculating Path…');
  clearAllHighlights();

  try {
    const { ok, data } = await apiFetch('/api/search', {
      method: 'POST',
      body: JSON.stringify({ algorithm, start, destination: dest, heuristic }),
    });

    if (!ok) { showError(data.message || 'Routing calculation failed.'); return; }

    state.lastSearch = data;
    displaySearchResult(data);

    if (data.status === 'success' && data.route) {
      highlightRoute(data.route);
      showSuccess(`Path solved: ${data.route.length - 1} edges • Total cost: ${data.total_cost}`);
    } else {
      showError('No open path connects these locations under current closures.');
    }
  } catch (e) {
    showError('Network request failed.');
    console.error(e);
  } finally {
    setLoading('btn-search', false);
  }
}

function displaySearchResult(data) {
  const panel = document.getElementById('search-result');
  const badgeWrap = document.getElementById('search-status-badge');
  if (badgeWrap) badgeWrap.innerHTML = statusPill(data.status);
  if (!panel) return;

  let segmentTable = '';
  if (data.status === 'success' && data.route && data.route.length > 1 && state.city) {
    segmentTable = `
      <div style="margin-top:14px">
        <label>Segment-by-Segment Travel Plan</label>
        <div class="table-wrapper">
          <table class="app-table">
            <thead>
              <tr><th>Leg</th><th>Road Segment</th><th>Segment Cost</th></tr>
            </thead>
            <tbody>
    `;
    for (let i = 0; i < data.route.length - 1; i++) {
      const u = data.route[i];
      const v = data.route[i + 1];
      const edge = state.city.edges.find(e => (e.source === u && e.target === v) || (e.source === v && e.target === u));
      const w = edge ? edge.weight : '—';
      segmentTable += `
        <tr>
          <td>Leg ${i + 1}</td>
          <td><b>${u}</b> → <b>${v}</b></td>
          <td>${w}</td>
        </tr>
      `;
    }
    segmentTable += `</tbody></table></div></div>`;
  }

  panel.innerHTML = `
    <div style="margin-bottom:12px">
      <label>Computed Route Sequence</label>
      <div class="route-trail-box">${formatRoute(data.route)}</div>
    </div>

    <div class="stat-summary-grid cols-2">
      <div class="stat-cell">
        <div class="stat-cell-label">Total Cost</div>
        <div class="stat-cell-value accent">${data.total_cost ?? '—'}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Runtime</div>
        <div class="stat-cell-value">${fmtNum(data.execution_time_ms, 3)} <span style="font-size:11px;color:var(--text-dim)">ms</span></div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Nodes Explored</div>
        <div class="stat-cell-value">${data.nodes_explored ?? '—'}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Nodes Generated</div>
        <div class="stat-cell-value">${data.nodes_generated ?? '—'}</div>
      </div>
    </div>

    ${segmentTable}
    ${data.message ? `<div style="margin-top:10px;font-size:11.5px;color:var(--warning)">${data.message}</div>` : ''}
  `;
  refreshIcons();
}

// ── Multi-Stop Tour Optimization ───────────────────────────────────
async function runOptimise() {
  const algorithm = document.getElementById('sel-opt-algorithm')?.value || 'simulated_annealing';
  const base      = document.getElementById('sel-base')?.value || 'A';
  const locations = getSelectedLocations();
  const seed      = parseInt(document.getElementById('opt-seed')?.value) || 42;

  if (!base) { showError('Please identify a rescue base node.'); return; }
  if (locations.length < 1) { showError('Select at least one destination incident location.'); return; }

  setLoading('btn-optimise', true, 'Optimizing Sequence…');
  clearTourHighlight();

  try {
    const { ok, data } = await apiFetch('/api/optimise', {
      method: 'POST',
      body: JSON.stringify({ algorithm, base, locations, seed }),
    });

    if (!ok) { showError(data.message || 'Tour optimization failed.'); return; }

    state.lastOptimise = data;
    displayOptResult(data);
    markBaseNode(base);

    if (data.status === 'success' && data.best_order) {
      await drawTourLegs(data.best_order);
      showSuccess(`Tour optimized: initial cost ${data.initial_cost} reduced to ${data.total_cost}.`);
    } else {
      showError('No feasible tour found (unreachable incident pair).');
    }
  } catch (e) {
    showError('Network communication failed.');
    console.error(e);
  } finally {
    setLoading('btn-optimise', false);
  }
}

async function drawTourLegs(tour) {
  const legs = [];
  for (let i = 0; i < tour.length - 1; i++) {
    try {
      const { data } = await apiFetch('/api/search', {
        method: 'POST',
        body: JSON.stringify({ algorithm: 'astar', start: tour[i], destination: tour[i + 1] }),
      });
      if (data.status === 'success' && data.route) legs.push(data.route);
    } catch (e) { /* skip */ }
  }
  highlightTour(tour, legs);
}

function displayOptResult(data) {
  const panel = document.getElementById('opt-result');
  if (!panel) return;

  const isOk = data.status === 'success';
  const improvement = (isOk && data.initial_cost && data.total_cost)
    ? (((data.initial_cost - data.total_cost) / data.initial_cost) * 100).toFixed(1)
    : null;

  panel.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
      <span style="font-weight:600;font-size:12px">Feasibility Status</span>
      ${statusPill(data.status)}
    </div>

    <div style="margin-bottom:10px">
      <label>Initial Visiting Order</label>
      <div class="route-trail-box" style="color:var(--text-muted)">${formatRoute(data.initial_order)}</div>
    </div>

    <div style="margin-bottom:12px">
      <label>Optimized Base-To-Base Tour</label>
      <div class="route-trail-box" style="color:#34d399">${data.best_order ? formatRoute(data.best_order) : '—'}</div>
    </div>

    <div class="stat-summary-grid cols-2" style="margin-bottom:14px">
      <div class="stat-cell">
        <div class="stat-cell-label">Initial Tour Cost</div>
        <div class="stat-cell-value" style="color:var(--text-dim)">${data.initial_cost ?? '—'}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Optimized Cost</div>
        <div class="stat-cell-value emerald">${data.total_cost ?? '—'}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Cost Reduction</div>
        <div class="stat-cell-value ${improvement && improvement > 0 ? 'emerald' : ''}">${improvement != null ? improvement + '%' : '—'}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Iterations</div>
        <div class="stat-cell-value">${data.iterations ?? '—'}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Compute Time</div>
        <div class="stat-cell-value">${fmtNum(data.execution_time_ms, 2)} <span style="font-size:11px;color:var(--text-dim)">ms</span></div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">RNG Seed</div>
        <div class="stat-cell-value">${data.seed ?? '—'}</div>
      </div>
    </div>

    ${renderMatrixTable(data.matrix)}
  `;
  refreshIcons();
}

function renderMatrixTable(matrix) {
  if (!matrix) return '';
  const nodes = Object.keys(matrix).sort();
  if (nodes.length === 0) return '';

  let html = `
    <div>
      <button type="button" class="collapse-btn" onclick="toggleMatrixTable(this)">
        <i data-lucide="chevron-right"></i>
        <span>Pairwise Shortest-Path Cost Matrix (UCS)</span>
      </button>
      <div class="collapse-body" id="matrix-container">
        <div class="table-wrapper">
          <table class="matrix-grid-table">
            <thead>
              <tr><th>Node</th>${nodes.map(n => `<th>${n}</th>`).join('')}</tr>
            </thead>
            <tbody>
  `;
  for (const u of nodes) {
    html += `<tr><th>${u}</th>`;
    for (const v of nodes) {
      const cost = matrix[u][v];
      if (cost === null) {
        html += `<td class="inf-val">—</td>`;
      } else if (u === v) {
        html += `<td class="diagonal">0</td>`;
      } else {
        html += `<td>${cost}</td>`;
      }
    }
    html += '</tr>';
  }
  html += `</tbody></table></div></div></div>`;
  return html;
}

function toggleMatrixTable(btn) {
  const target = document.getElementById('matrix-container');
  if (!target) return;
  const isOpen = target.classList.contains('open');
  target.classList.toggle('open', !isOpen);
  const icon = btn.querySelector('i');
  if (icon) {
    icon.setAttribute('data-lucide', isOpen ? 'chevron-right' : 'chevron-down');
    refreshIcons();
  }
}

// ── Head-to-Head Comparison ────────────────────────────────────────
async function runComparison() {
  const start = document.getElementById('sel-start')?.value;
  const dest  = document.getElementById('sel-destination')?.value;
  const heuristic = document.getElementById('sel-heuristic')?.value || 'euclidean';
  const algos = Array.from(document.querySelectorAll('#cmp-algo-checks input:checked')).map(cb => cb.value);

  if (!start || !dest) { showError('Select valid endpoints.'); return; }
  if (algos.length === 0) { showError('Check at least one algorithm to benchmark.'); return; }

  setLoading('btn-compare', true, 'Evaluating Algorithms…');
  clearRouteHighlight();

  try {
    const promises = algos.map(alg =>
      apiFetch('/api/search', {
        method: 'POST',
        body: JSON.stringify({ algorithm: alg, start, destination: dest, heuristic }),
      })
    );

    const responses = await Promise.all(promises);
    const results = responses.map((r, i) => ({ algorithm: algos[i], result: r.data }));
    state.comparisonResults = results;
    renderComparisonTable(results);
    showSuccess(`Comparison complete across ${algos.length} algorithm(s). Click any row to preview its route on the map.`);
  } catch (e) {
    showError('Comparison execution failed.');
    console.error(e);
  } finally {
    setLoading('btn-compare', false);
  }
}

function renderComparisonTable(results) {
  const tbody = document.getElementById('cmp-tbody');
  if (!tbody) return;

  const validCosts = results
    .filter(r => r.result.status === 'success' && r.result.total_cost != null)
    .map(r => r.result.total_cost);
  const minCost = validCosts.length ? Math.min(...validCosts) : null;

  tbody.innerHTML = '';
  results.forEach((item, idx) => {
    const r = item.result;
    const isBest = (minCost !== null && r.total_cost === minCost && r.status === 'success');
    const tr = document.createElement('tr');
    tr.className = 'clickable' + (isBest ? ' best-metric' : '');
    if (idx === 0) tr.classList.add('selected');

    const meta = ALGO_METADATA[item.algorithm] || { label: item.algorithm, guarantee: '' };

    tr.innerHTML = `
      <td>
        <div style="font-weight:600">${meta.label}</div>
        <div class="${meta.badgeClass}">${meta.guarantee}</div>
      </td>
      <td>${statusPill(r.status)}</td>
      <td style="font-weight:700">${r.total_cost != null ? `${r.total_cost}${isBest ? ' (Lowest)' : ''}` : '—'}</td>
      <td>${fmtNum(r.execution_time_ms, 3)}</td>
      <td>${r.nodes_explored ?? '—'}</td>
      <td>${r.nodes_generated ?? '—'}</td>
      <td>${r.status === 'success' ? '<span class="pill pill-success">Valid</span>' : '<span class="pill pill-danger">Invalid</span>'}</td>
    `;

    tr.addEventListener('click', () => {
      document.querySelectorAll('#cmp-tbody tr').forEach(row => row.classList.remove('selected'));
      tr.classList.add('selected');
      if (r.route) {
        highlightComparisonRoute(r.route);
        showInfo(`Showing path computed by ${meta.label}: ${formatRoute(r.route)}`);
      }
    });

    tbody.appendChild(tr);
  });

  const firstSuccess = results.find(r => r.result.status === 'success' && r.result.route);
  if (firstSuccess) highlightComparisonRoute(firstSuccess.result.route);
  refreshIcons();
}

// ── Pure-Data Benchmarking (No Chart Distributions) ─────────────────
async function runBenchmark() {
  const mode = document.querySelector('input[name="bench-mode"]:checked')?.value || 'search';
  const repeats = parseInt(document.getElementById('bench-repeats')?.value) || 5;
  const seeds = parseInt(document.getElementById('bench-seeds')?.value) || 15;

  const algoContainerId = mode === 'search' ? 'bench-algos-search' : 'bench-algos-opt';
  const algorithms = Array.from(document.querySelectorAll(`#${algoContainerId} input:checked`)).map(cb => cb.value);

  if (algorithms.length === 0) {
    showError('Select at least one algorithm for the benchmark suite.');
    return;
  }

  setLoading('btn-benchmark', true, 'Running Test Suite…');

  const payload = {
    mode,
    algorithms,
    repeats: mode === 'search' ? repeats : undefined,
    seeds: mode === 'optimise' ? Array.from({ length: seeds }, (_, i) => i) : undefined,
  };

  if (mode === 'optimise') {
    payload.base = 'A';
    payload.locations = ['C', 'D', 'H'];
  }

  try {
    const { ok, data } = await apiFetch('/api/benchmark', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (!ok) { showError(data.message || 'Benchmark failed.'); return; }

    state.lastBenchmark = data;
    renderBenchmarkTable(data, mode);
    const csvBtn = document.getElementById('csv-btn');
    if (csvBtn) csvBtn.removeAttribute('aria-disabled');
    showSuccess(`Benchmark complete: ${data.rows.length} execution trials recorded.`);
  } catch (e) {
    showError('Benchmark execution failed.');
    console.error(e);
  } finally {
    setLoading('btn-benchmark', false);
  }
}

function renderBenchmarkTable(data, mode) {
  const container = document.getElementById('bench-summary-table');
  if (!container || !data.summary || data.summary.length === 0) {
    if (container) container.innerHTML = '<div class="empty-state"><p>No benchmark records available.</p></div>';
    return;
  }

  const summary = data.summary;
  const keys = Object.keys(summary[0]).filter(k => k !== 'pair');

  let html = `
    <table class="app-table">
      <thead>
        <tr>
  `;
  if (summary[0].pair) html += `<th>Test Pair</th>`;
  html += keys.map(k => `<th>${k.replace(/_/g, ' ')}</th>`).join('');
  html += `
        </tr>
      </thead>
      <tbody>
  `;

  for (const row of summary) {
    html += '<tr>';
    if (row.pair) html += `<td style="font-family:var(--font-mono);font-weight:600">${row.pair}</td>`;
    for (const k of keys) {
      let v = row[k];
      if (typeof v === 'number') v = v.toFixed(3);
      html += `<td>${v ?? '—'}</td>`;
    }
    html += '</tr>';
  }
  html += `</tbody></table>`;
  container.innerHTML = html;
  refreshIcons();
}

// ── Dropdown & Input Listeners ─────────────────────────────────────
function onAlgorithmChange() {
  const algSel = document.getElementById('sel-algorithm');
  const hSel   = document.getElementById('sel-heuristic');
  const noteEl = document.getElementById('algo-guarantee-note');
  if (!algSel) return;

  const alg = algSel.value;
  const informed = ['astar', 'ida_star', 'greedy'];
  if (hSel) hSel.disabled = !informed.includes(alg);

  if (noteEl) {
    const meta = ALGO_METADATA[alg];
    if (meta) {
      noteEl.textContent = meta.guarantee;
      noteEl.className = `input-hint ${meta.badgeClass}`;
    }
  }
}

function onBaseChange() {
  if (state.city) populateLocationCheckboxes(state.city);
  const baseSel = document.getElementById('sel-base');
  if (baseSel) markBaseNode(baseSel.value);
}

function onBenchModeChange() {
  const mode = document.querySelector('input[name="bench-mode"]:checked')?.value || 'search';
  const searchAlgos = document.getElementById('bench-algos-search');
  const optAlgos    = document.getElementById('bench-algos-opt');
  const repeatsRow  = document.getElementById('bench-repeats-row');
  const seedsRow    = document.getElementById('bench-seeds-row');

  if (searchAlgos) searchAlgos.style.display = mode === 'search' ? 'grid' : 'none';
  if (optAlgos)    optAlgos.style.display    = mode === 'optimise' ? 'grid' : 'none';
  if (repeatsRow)  repeatsRow.style.display  = mode === 'search' ? 'block' : 'none';
  if (seedsRow)    seedsRow.style.display    = mode === 'optimise' ? 'block' : 'none';
}

// ── DOM Initializer ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  document.getElementById('btn-search')?.addEventListener('click', runSearch);
  document.getElementById('btn-block')?.addEventListener('click', blockRoad);
  document.getElementById('btn-reopen')?.addEventListener('click', reopenRoad);
  document.getElementById('btn-reset')?.addEventListener('click', resetScenario);
  document.getElementById('btn-optimise')?.addEventListener('click', runOptimise);
  document.getElementById('btn-compare')?.addEventListener('click', runComparison);
  document.getElementById('btn-benchmark')?.addEventListener('click', runBenchmark);

  document.getElementById('sel-algorithm')?.addEventListener('change', onAlgorithmChange);
  document.getElementById('sel-base')?.addEventListener('change', onBaseChange);

  document.querySelectorAll('input[name="bench-mode"]').forEach(r => {
    r.addEventListener('change', onBenchModeChange);
  });

  await loadCity();

  onAlgorithmChange();
  onBenchModeChange();
  refreshIcons();
});
