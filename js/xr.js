(() => {
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

  function scanLabels() {
    labelMap.clear();
    typeCounters.clear();
    document.querySelectorAll('.text_cell_render, .jp-RenderedHTMLCommon').forEach(cell => {
      const walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const re = /@([A-Za-z]+:)?([A-Za-z0-9:_\-]+)/g;
        let m;
        while ((m = re.exec(walker.currentNode.data)) !== null) {
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
    });
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
        span.innerHTML = `<a id="${id}">${formatLabel(type, n)}</a>` +
          `<span style="display:none">\$begin:math:text$\\\\label{${id}}\\$end:math:text$</span>`;
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
    document.querySelectorAll('.text_cell_render, .jp-RenderedHTMLCommon').forEach(walk);
    if (window.MathJax?.typesetPromise) {
      MathJax.typesetPromise();
    } else if (window.MathJax?.Hub?.Queue) {
      MathJax.Hub.Queue(['Typeset', MathJax.Hub]);
    }
  }

  function processAll() {
    scanLabels();
    rewriteAll();
  }

  if (typeof Jupyter !== 'undefined' && Jupyter.notebook?.events) {
    Jupyter.notebook.events.on('rendered.MarkdownCell', () => processAll());
  }

  if (typeof MutationObserver !== 'undefined') {
    const obs = new MutationObserver(() => processAll());
    obs.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', processAll);
  } else {
    processAll();
  }
})();

