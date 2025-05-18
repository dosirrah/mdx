(() => {
  const labelMap = new Map();
  const typeCounters = new Map();

  const TAGGABLE_TYPES = new Set(['eq', 'Eq']);

  function toId(type, id) {
    return type ? `${type}:${id}` : id;
  }

  function rewriteText(textNode) {
    const re = /(@|#)([A-Za-z]+:)?([A-Za-z0-9:_\-]+)(!?)/g;
    let m, last = 0;
    const frag = document.createDocumentFragment();

    const data = textNode.data;

    while ((m = re.exec(data)) !== null) {
      const [full, sym, rawType, id, bang] = m;
      const type = rawType ? rawType.slice(0, -1) : null;
      const key = toId(type, id);

      frag.appendChild(document.createTextNode(data.slice(last, m.index)));
      last = m.index + full.length;

      if (sym === '@') {
        let n;
        if (!labelMap.has(key)) {
          if (type) {
            n = (typeCounters.get(type) ?? 0) + 1;
            typeCounters.set(type, n);
          } else {
            n = (typeCounters.get('_global') ?? 0) + 1;
            typeCounters.set('_global', n);
          }
          labelMap.set(key, { type, n, id });
        } else {
          n = labelMap.get(key).n;
        }

        const span = document.createElement('span');
        span.innerHTML = `<a id="${id}">${formatLabel(type, n)}</a>` +
          `<span style="display:none">\$begin:math:text$\\\\label{${id}}\\$end:math:text$</span>`;
        frag.appendChild(span);
      }

      if (sym === '#') {
        const entry = labelMap.get(key);
        const n = entry?.n ?? '??';
        const label = formatLabel(entry?.type ?? type, n, bang === '!');
        const a = document.createElement('a');
        a.href = `#${id}`;
        a.textContent = label;
        frag.appendChild(a);
      }
    }

    frag.appendChild(document.createTextNode(data.slice(last)));
    textNode.parentNode.replaceChild(frag, textNode);
  }

  function formatLabel(type, n, raw = false) {
    if (type && TAGGABLE_TYPES.has(type.toLowerCase())) {
      return raw ? `${n}` : `(${n})`;
    }
    return raw ? `${n}` : type ? `${type} ${n}` : `${n}`;
  }

  function walk(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      rewriteText(node);
    } else {
      node.childNodes.forEach(walk);
    }
  }

  function rewriteNode(node) {
    walk(node);
  }

  function processAll() {
    document.querySelectorAll('.text_cell_render, .jp-RenderedHTMLCommon')
      .forEach(rewriteNode);

    if (window.MathJax) {
      if (window.MathJax.typesetPromise) {
        MathJax.typesetPromise();
      } else if (window.MathJax.Hub?.Queue) {
        MathJax.Hub.Queue(['Typeset', MathJax.Hub]);
      }
    }
  }

  if (typeof Jupyter !== 'undefined' && Jupyter.notebook?.events) {
    Jupyter.notebook.events.on('rendered.MarkdownCell', (evt, data) => {
      rewriteNode(data.cell.element[0]);
      if (window.MathJax?.Hub?.Queue) {
        MathJax.Hub.Queue(['Typeset', MathJax.Hub]);
      }
    });
  }

  if (typeof MutationObserver !== 'undefined') {
    const observer = new MutationObserver(muts => {
      muts.forEach(m => {
        m.addedNodes?.forEach(node => {
          if (node instanceof HTMLElement &&
              node.classList.contains('jp-RenderedHTMLCommon')) {
            rewriteNode(node);
            if (window.MathJax?.typesetPromise) {
              MathJax.typesetPromise();
            }
          }
        });
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', processAll);
  } else {
    processAll();
  }
})();
