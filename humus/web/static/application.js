document.addEventListener("DOMContentLoaded", (loadEvent) => {
  const form = document.getElementById("form");
  const input = document.getElementById("text-input");
  const display = document.getElementById("text-display");

  form.addEventListener("submit", (submitEvent) => {
    input.value = display.innerText;
  });

  display.addEventListener('beforeinput', (e) => {
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    const range = sel.getRangeAt(0);

    let node = range.startContainer;
    let oldSpan = null;
    while (node && node !== display) {
      if (node.nodeType === Node.ELEMENT_NODE && node.classList.contains('old')) {
        oldSpan = node;
        break;
      }
      node = node.parentNode;
    }

    if (!oldSpan) return;

    e.preventDefault();

    const offset = range.startOffset;
    const fullText = range.startContainer.textContent;
    const before = fullText.slice(0, offset);
    const after = fullText.slice(offset);

    const userSpan = document.createElement('span');
    userSpan.className = 'user-edit';
    userSpan.textContent = '';

    const parent = oldSpan.parentNode;
    const oldClass = oldSpan.className

    if (before) {
      const spanBefore = document.createElement('span');
      spanBefore.className = oldClass;
      spanBefore.textContent = before;
      parent.insertBefore(spanBefore, oldSpan);
    }

    parent.insertBefore(userSpan, oldSpan);

    if (after) {
      const spanAfter = document.createElement('span');
      spanAfter.className = oldClass;
      spanAfter.textContent = after;
      parent.insertBefore(spanAfter, oldSpan);
    }

    parent.removeChild(oldSpan);

    const newRange = document.createRange();
    newRange.setStart(userSpan, 0);
    newRange.collapse(true);
    sel.removeAllRanges();
    sel.addRange(newRange);

    if (e.data) {
      document.execCommand('insertText', false, e.data);
    }
  });

  display.addEventListener('input', () => {
    const sel = window.getSelection();
    const range = sel.rangeCount ? sel.getRangeAt(0) : null;
    Array.from(display.childNodes).forEach(node => {
      if (node.nodeType === Node.TEXT_NODE && node.textContent.length > 0) {
        const span = document.createElement('span');
        span.className = 'new';
        display.insertBefore(span, node);
        span.appendChild(node);
      }
    });

    if (range) {
      sel.removeAllRanges();
      sel.addRange(range);
    }
  });
});
