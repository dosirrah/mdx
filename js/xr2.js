(() => {
  // ----------------------------------------------------------------------------
  // xr.js — Cross-reference support for classic Notebook and JupyterLab
  // ----------------------------------------------------------------------------

  // Global state to avoid reinstallation
  if (window.xrBooted) return;
  window.xrBooted = true;

  const labelMap = new Map();
  const typeCounters = new Map();
  const TAGGABLE_TYPES = new Set(['eq', 'Eq']);

  function toId(type, id) {
    return type ? `${type}:${id}` : id;
  }

  function formatLabel(type, n, raw = false) {
    if (type && TAGGABLE_TYPES.has(type.toLowerCase())) {
      return raw ? `${n}` : `(${n})`;
    }
    return raw ? `${n}` : type ? `${type} ${n}` : `${n}`;
  }

  function rewriteText(textNode) {
    const re = /(@|#)([A-Za-z]+:)?([A-Za-z0-9:_\-]+)(!?)/g;
    const data = textNode.data;
    const frag = document.createDocumentFragment();
    let last = 0, m;

    while ((m = re.exec(data)) !== null) {
      const [full, sym, rawType, id, bang] = m;
      const type = rawType ? rawType.slice(0, -1) : null;
      const key = toId(type, id);
      const entry = labelMap.get(key);

      frag.appendChild(document.createTextNode(data.slice(last, m.index)));
      last = m.index + full.length;

      if (sym === '@') {
        const n = entry?.n ?? '??';
        const span = document.createElement('span');
        span.innerHTML =
          `<a id="${id}">${formatLabel(type, n)}</a>` +
          `<span style="display:none">\\label{${id}}</span>`;
        frag.appendChild(span);
      }

      if (sym === '#') {
        const n = entry?.n ?? '??';
        const label = formatLabel(entry?.type ?? type, n, bang === '!');
        const a = document.createElement('a');
        a.href = `#${id}`;
        a.textContent = label;
        frag.appendChild(a);
      }
    }

    frag.appendChild(document.createTextNode(data.slice(last)));
    textNode.parentNode?.replaceChild(frag, textNode);
  }

  function walk(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      rewriteText(node);
    } else {
      node.childNodes.forEach(walk);
    }
  }

  function rewriteAll() {
    document
      .querySelectorAll('.text_cell_render, .jp-RenderedHTMLCommon')
      .forEach(walk);
    if (window.MathJax?.typesetPromise) {
      MathJax.typesetPromise();
    } else if (window.MathJax?.Hub?.Queue) {
      MathJax.Hub.Queue(['Typeset', MathJax.Hub]);
    }
  }

  // ---------------------------------------------------------------------------
  // Classic Notebook: scan from cell.get_text()
  // ---------------------------------------------------------------------------
  function scanClassic() {
    labelMap.clear();
    typeCounters.clear();
    if (!window.Jupyter?.notebook?.get_cells) return;

    const cells = Jupyter.notebook.get_cells();
    for (const cell of cells) {
      if (cell.cell_type !== 'markdown') continue;
      const text = cell.get_text();
      const re = /@([A-Za-z]+:)?([A-Za-z0-9:_\-]+)/g;
      let m;
      while ((m = re.exec(text)) !== null) {
        const rawType = m[1], id = m[2];
        const type = rawType ? rawType.slice(0, -1) : null;
        const key = toId(type, id);
        if (!labelMap.has(key)) {
          const counterKey = type ?? '_global';
          const n = (typeCounters.get(counterKey) ?? 0) + 1;
          typeCounters.set(counterKey, n);
          labelMap.set(key, { type, id, n });
        }
      }
    }
  }

  // ---------------------------------------------------------------------------
  // JupyterLab: scan from notebookPanel.model.cells
  // ---------------------------------------------------------------------------
  function scanLab(notebookPanel) {
    labelMap.clear();
    typeCounters.clear();
    if (!notebookPanel?.content?.widgets) return;

    const cells = notebookPanel.content.widgets;
    for (const cell of cells) {
      if (cell.model?.type !== 'markdown') continue;
      const text = cell.model.value.text;
      const re = /@([A-Za-z]+:)?([A-Za-z0-9:_\-]+)/g;
      let m;
      while ((m = re.exec(text)) !== null) {
        const rawType = m[1], id = m[2];
        const type = rawType ? rawType.slice(0, -1) : null;
        const key = toId(type, id);
        if (!labelMap.has(key)) {
          const counterKey = type ?? '_global';
          const n = (typeCounters.get(counterKey) ?? 0) + 1;
          typeCounters.set(counterKey, n);
          labelMap.set(key, { type, id, n });
        }
      }
    }
  }

  function processAll(notebookPanel = null) {
    if (notebookPanel) scanLab(notebookPanel);
    else scanClassic();
    rewriteAll();
  }

  // ---------------------------------------------------------------------------
  // Classic Notebook hook
  // ---------------------------------------------------------------------------
  if (window.Jupyter?.notebook?.events) {
    Jupyter.notebook.events.on('rendered.MarkdownCell', () => processAll());
  }

  // ---------------------------------------------------------------------------
  // JupyterLab hook — zero-install
  // ---------------------------------------------------------------------------
  (async () => {
    try {
      if (!window.jupyterapp || !window.jupyterapp.started || window.xrLabHookInstalled) return;
      await window.jupyterapp.started;

      const nb = await import('@jupyterlab/notebook');
      const { INotebookTracker } = nb;
      const tracker = window.jupyterapp.serviceManager?.get?.(INotebookTracker.id);
      if (!tracker) return;

      function wireCell(cell, panel) {
        if (cell.model?.type !== 'markdown' || cell._xrWired) return;
        cell._xrWired = true;
        cell.renderedChanged.connect(() => {
          if (cell.rendered) processAll(panel);
        });
      }

      // Handle existing notebooks
      tracker.forEach(panel => {
        panel.content.widgets.forEach(c => wireCell(c, panel));
        panel.content.model?.cells.changed.connect(() =>
          panel.content.widgets.forEach(c => wireCell(c, panel))
        );
      });

      // Handle future notebooks
      tracker.widgetAdded.connect((_, panel) => {
        panel.content.widgets.forEach(c => wireCell(c, panel));
        panel.content.model?.cells.changed.connect(() =>
          panel.content.widgets.forEach(c => wireCell(c, panel))
        );
      });

      window.xrLabHookInstalled = true;
      console.log('[xr] JupyterLab cross-reference hook installed');
    } catch (err) {
      console.warn('[xr] Could not install JupyterLab hook:', err);
    }
  })();

  // ---------------------------------------------------------------------------
  // Fallback: run once on DOM load
  // ---------------------------------------------------------------------------
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => processAll());
  } else {
    processAll();
  }

})();
