(() => {
  const idMap = new Map();
  let counter = 0;

  function rewriteNode(cellElement) {
    const re = /(@|#)([A-Za-z0-9:_\-]+)/g;

    function transformText(textNode) {
      const data = textNode.data;
      const frag = document.createDocumentFragment();
      let last = 0;
      let m;

      while ((m = re.exec(data)) !== null) {
        const [full, kind, id] = m;
        frag.appendChild(document.createTextNode(data.slice(last, m.index)));
        last = m.index + full.length;

        if (kind === '@') {
          if (!idMap.has(id)) idMap.set(id, ++counter);
          const num = idMap.get(id);
          const span = document.createElement('span');
          span.textContent = num;
          span.insertAdjacentHTML(
            'beforeend',
            `<span style="display:none">\$begin:math:text$\\\\label{${id}}\\$end:math:text$</span>`
          );
          frag.appendChild(span);
        } else {
          const num = idMap.get(id) ?? '??';
          const span = document.createElement('span');
          span.textContent = num;
          span.insertAdjacentHTML(
            'beforeend',
            `\$begin:math:text$\\\\ref{${id}}\\$end:math:text$`
          );
          frag.appendChild(span);
        }
      }
      frag.appendChild(document.createTextNode(data.slice(last)));
      textNode.parentNode?.replaceChild(frag, textNode);
    }

    function walk(n) {
      if (n.nodeType === Node.TEXT_NODE) {
        transformText(n);
      } else {
        n.childNodes.forEach(walk);
      }
    }

    walk(cellElement);
  }

  function processAll() {
    // Classic Jupyter and JupyterLab-compatible scan
    document.querySelectorAll('.text_cell_render, .jp-RenderedHTMLCommon')
      .forEach(rewriteNode);

    if (window.MathJax) {
      if (window.MathJax.typesetPromise) {
        MathJax.typesetPromise(); // MathJax v3
      } else if (window.MathJax.Hub?.Queue) {
        MathJax.Hub.Queue(['Typeset', MathJax.Hub]); // MathJax v2
      }
    }
  }

  // Re-run on render (classic Notebook)
  if (typeof Jupyter !== 'undefined' && Jupyter.notebook?.events) {
    Jupyter.notebook.events.on('rendered.MarkdownCell', (evt, data) => {
      rewriteNode(data.cell.element[0]);
      if (window.MathJax?.Hub?.Queue) {
        MathJax.Hub.Queue(['Typeset', MathJax.Hub]);
      }
    });
  }

  // For JupyterLab: observe dynamic Markdown rendering
  if (typeof MutationObserver !== 'undefined') {
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        m.addedNodes?.forEach(node => {
          if (node instanceof HTMLElement &&
              node.classList.contains('jp-RenderedHTMLCommon')) {
            rewriteNode(node);
            if (window.MathJax?.typesetPromise) {
              MathJax.typesetPromise();
            }
          }
        });
      }
    });
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  // Initial pass
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', processAll);
  } else {
    processAll();
  }

})();
