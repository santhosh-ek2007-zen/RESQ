// app/static/js/graph.js — High-performance Cytoscape graph visualization for RESQ

let cy = null;

const GRAPH_STYLESHEET = [
  {
    selector: 'node',
    style: {
      'label': 'data(label)',
      'background-color': '#1a2230',
      'border-color': '#334155',
      'border-width': 2,
      'color': '#f8fafc',
      'font-size': '11.5px',
      'font-weight': '600',
      'text-valign': 'center',
      'text-halign': 'center',
      'width': 54,
      'height': 54,
      'text-wrap': 'wrap',
      'text-max-width': '48px',
      'text-margin-y': 0,
      'transition-property': 'background-color, border-color, border-width, width, height',
      'transition-duration': '0.15s',
    }
  },
  {
    selector: 'node.base-node',
    style: {
      'background-color': '#1f2937',
      'border-color': '#f59e0b',
      'border-width': 3,
      'width': 58,
      'height': 58,
    }
  },
  {
    selector: 'node.route-node',
    style: {
      'background-color': '#1e3a5f',
      'border-color': '#3b82f6',
      'border-width': 3.5,
      'z-index': 10,
    }
  },
  {
    selector: 'node.tour-node',
    style: {
      'background-color': '#064e3b',
      'border-color': '#10b981',
      'border-width': 3.5,
      'z-index': 10,
    }
  },
  {
    selector: 'node.start-node',
    style: {
      'background-color': '#064e3b',
      'border-color': '#10b981',
      'border-width': 3.5,
      'width': 58,
      'height': 58,
    }
  },
  {
    selector: 'node.end-node',
    style: {
      'background-color': '#450a0a',
      'border-color': '#ef4444',
      'border-width': 3.5,
      'width': 58,
      'height': 58,
    }
  },
  {
    selector: 'edge',
    style: {
      'label': 'data(label)',
      'line-color': '#475569',
      'width': 2.5,
      'font-size': '11px',
      'font-weight': '600',
      'color': '#cbd5e1',
      'text-background-color': '#0f141c',
      'text-background-opacity': 0.9,
      'text-background-padding': '3px',
      'text-background-shape': 'roundrectangle',
      'text-border-color': '#243042',
      'text-border-width': 1,
      'text-border-opacity': 0.7,
      'curve-style': 'bezier',
      'target-arrow-shape': 'none',
      'transition-property': 'line-color, width, opacity',
      'transition-duration': '0.15s',
    }
  },
  {
    selector: 'edge.blocked',
    style: {
      'line-color': '#ef4444',
      'line-style': 'dashed',
      'line-dash-pattern': [7, 4],
      'opacity': 0.5,
      'width': 2,
      'color': '#f87171',
    }
  },
  {
    selector: 'edge.route-edge',
    style: {
      'line-color': '#3b82f6',
      'width': 5,
      'opacity': 1,
      'z-index': 10,
    }
  },
  {
    selector: 'edge.tour-edge',
    style: {
      'line-color': '#10b981',
      'width': 4,
      'opacity': 1,
      'line-style': 'dashed',
      'line-dash-pattern': [8, 4],
      'z-index': 9,
    }
  },
];

function edgeId(u, v) {
  return [u, v].sort().join('-');
}

function renderGraph(cityJson) {
  const container = document.getElementById('cy');
  if (!container) return;

  const elements = [];

  for (const node of cityJson.nodes) {
    elements.push({
      data: { id: node.id, label: `${node.id}\n${node.label}` },
      position: { x: node.x * 12 + 60, y: node.y * 8.5 + 60 },
      classes: '',
    });
  }

  for (const edge of cityJson.edges) {
    elements.push({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        weight: edge.weight,
        label: `${edge.weight}`,
        blocked: edge.blocked,
      },
      classes: edge.blocked ? 'blocked' : '',
    });
  }

  if (cy) {
    cy.destroy();
  }

  cy = cytoscape({
    container: container,
    elements: elements,
    style: GRAPH_STYLESHEET,
    layout: { name: 'preset', fit: true, padding: 50 },
    userZoomingEnabled: true,
    userPanningEnabled: true,
    minZoom: 0.35,
    maxZoom: 3.0,
    wheelSensitivity: 0.2,
  });

  setTimeout(() => {
    if (cy) {
      cy.resize();
      cy.fit(null, 45);
    }
  }, 50);

  // Click on edge to pre-select endpoints
  cy.on('tap', 'edge', function(evt) {
    const data = evt.target.data();
    const srcSel = document.getElementById('road-source');
    const tgtSel = document.getElementById('road-target');
    if (srcSel && tgtSel) {
      srcSel.value = data.source;
      tgtSel.value = data.target;
      if (typeof showInfo === 'function') {
        showInfo(`Selected segment: ${data.source} ↔ ${data.target} (Travel cost: ${data.weight})`);
      }
    }
  });

  // Click on node
  cy.on('tap', 'node', function(evt) {
    const nodeId = evt.target.id();
    const startSel = document.getElementById('sel-start');
    const destSel  = document.getElementById('sel-destination');
    const baseSel  = document.getElementById('sel-base');

    if (startSel && destSel) {
      if (!startSel.value || (startSel.value && destSel.value)) {
        startSel.value = nodeId;
      } else if (startSel.value && !destSel.value && startSel.value !== nodeId) {
        destSel.value = nodeId;
      }
    } else if (baseSel) {
      baseSel.value = nodeId;
      if (typeof onBaseChange === 'function') onBaseChange();
    }
  });
}

function updateGraph(cityJson) {
  renderGraph(cityJson);
}

function highlightRoute(route) {
  if (!cy || !route || route.length === 0) return;

  clearRouteHighlight();

  for (const nodeId of route) {
    const node = cy.getElementById(nodeId);
    if (node) node.addClass('route-node');
  }

  for (let i = 0; i < route.length - 1; i++) {
    const eid = edgeId(route[i], route[i + 1]);
    const edge = cy.getElementById(eid);
    if (edge) edge.addClass('route-edge');
  }

  if (route.length > 0) {
    cy.getElementById(route[0]).addClass('start-node');
    cy.getElementById(route[route.length - 1]).addClass('end-node');
  }
}

function highlightTour(tour, legRoutes) {
  if (!cy || !tour || tour.length < 2) return;

  clearTourHighlight();

  for (let i = 0; i < tour.length; i++) {
    const node = cy.getElementById(tour[i]);
    if (node) node.addClass('tour-node');
  }

  if (legRoutes && legRoutes.length > 0) {
    for (const legRoute of legRoutes) {
      for (let i = 0; i < legRoute.length - 1; i++) {
        const eid = edgeId(legRoute[i], legRoute[i + 1]);
        const edge = cy.getElementById(eid);
        if (edge) edge.addClass('tour-edge');
      }
    }
  } else {
    for (let i = 0; i < tour.length - 1; i++) {
      const eid = edgeId(tour[i], tour[i + 1]);
      const edge = cy.getElementById(eid);
      if (edge) edge.addClass('tour-edge');
    }
  }
}

function clearRouteHighlight() {
  if (!cy) return;
  cy.nodes().removeClass('route-node start-node end-node');
  cy.edges().removeClass('route-edge');
}

function clearTourHighlight() {
  if (!cy) return;
  cy.nodes().removeClass('tour-node');
  cy.edges().removeClass('tour-edge');
}

function clearAllHighlights() {
  clearRouteHighlight();
  clearTourHighlight();
  if (cy) cy.nodes().removeClass('base-node');
}

function markBaseNode(nodeId) {
  if (!cy) return;
  cy.nodes().removeClass('base-node');
  if (nodeId) cy.getElementById(nodeId).addClass('base-node');
}

function highlightComparisonRoute(route) {
  if (!cy || !route) return;
  clearRouteHighlight();
  highlightRoute(route);
}

// ── Viewport Control Functions ─────────────────────────────────────
function zoomIn() {
  if (!cy) return;
  cy.zoom({ level: cy.zoom() * 1.25, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
}

function zoomOut() {
  if (!cy) return;
  cy.zoom({ level: cy.zoom() * 0.8, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
}

function fitGraph() {
  if (!cy) return;
  cy.fit(null, 45);
}

function resetGraph() {
  if (!cy) return;
  cy.reset();
  cy.fit(null, 45);
}

window.addEventListener('resize', () => {
  if (cy) {
    cy.resize();
    cy.fit(null, 45);
  }
});
