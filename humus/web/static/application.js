let panning = false,
  draggable = null,
  tx = 0,
  ty = 0,
  scale = 1,
  dragOffsetX,
  dragOffsetY,
  panStartX,
  panStartY,
  panStartTx,
  panStartTy;
const MIN_SCALE = 0.1,
  MAX_SCALE = 8,
  RESIZE_HANDLE_SIZE = 17;

function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

const saveContent = async (id, display) => {
  const last = display.dataset["lastSaved"];
  const content = display.innerText;
  if (last === content) return;
  data = new FormData();
  data.set("text", content);
  await fetch(`${id}`, {
    method: "POST",
    body: data,
  });
  display.dataset["lastSaved"] = content;
  unsavedChanges = document.querySelector(".unsaved-changes");
  if (unsavedChanges) {
    unsavedChanges.classList.remove("unsaved-changes");
  }
};

const debouncedSaveContent = debounce(saveContent, 1500);

function setupWorldScroll() {
  const world = document.getElementById("world");
  const wrapper = document.getElementById("wrapper");

  function applyTransform() {
    world.style.transform = `translate(${tx}px,${ty}px) scale(${scale})`;
  }

  function clampScale(s) {
    return Math.min(MAX_SCALE, Math.max(MIN_SCALE, s));
  }

  wrapper.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      const rect = wrapper.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const delta = e.deltaY < 0 ? 1.1 : 0.909;
      const newScale = clampScale(scale * delta);
      tx = mx - (mx - tx) * (newScale / scale);
      ty = my - (my - ty) * (newScale / scale);
      scale = newScale;
      applyTransform();
    },
    { passive: false },
  );

  wrapper.addEventListener("mousedown", (e) => {
    if (e.target.closest(".draggable")) return;
    panning = true;
    panStartX = e.clientX;
    panStartY = e.clientY;
    panStartTx = tx;
    panStartTy = ty;
    wrapper.classList.add("panning");
  });

  window.addEventListener("mousemove", (e) => {
    if (panning) {
      tx = panStartTx + (e.clientX - panStartX);
      ty = panStartTy + (e.clientY - panStartY);
      applyTransform();
    }

    if (draggable) {
      const rect = wrapper.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      draggable.style.left = (mx - tx) / scale - dragOffsetX + "px";
      draggable.style.top = (my - ty) / scale - dragOffsetY + "px";
    }
  });

  window.addEventListener("mouseup", async () => {
    panning = false;
    wrapper.classList.remove("panning");
    if (draggable) {
      draggable.classList.remove("dragging");
      data = new FormData();
      const id = draggable.dataset["recordId"];
      data.set("x", parseInt(draggable.style.left));
      data.set("y", parseInt(draggable.style.top));
      await fetch(`/${id}`, {
        method: "POST",
        body: data,
      });
      draggable = null;
    }
  });

  wrapper.addEventListener(
    "touchstart",
    (e) => {
      if (e.touches.length === 1) {
        if (e.target.closest(".draggable")) return;
        panning = true;
        panStartX = e.touches[0].clientX;
        panStartY = e.touches[0].clientY;
        panStartTx = tx;
        panStartTy = ty;
      }
    },
    { passive: true },
  );

  wrapper.addEventListener(
    "touchmove",
    (e) => {
      if (e.touches.length === 1 && panning) {
        e.preventDefault();
        tx = panStartTx + (e.touches[0].clientX - panStartX);
        ty = panStartTy + (e.touches[0].clientY - panStartY);
        applyTransform();
      }

      if (e.touches.length === 1 && draggable) {
        const rect = wrapper.getBoundingClientRect();
        const mx = e.touches[0].clientX - rect.left;
        const my = e.touches[0].clientY - rect.top;

        draggable.style.left = (mx - tx) / scale - dragOffsetX + "px";
        draggable.style.top = (my - ty) / scale - dragOffsetY + "px";
      }
    },
    { passive: false },
  );

  wrapper.addEventListener("touchend", async () => {
    panning = false;
    if (draggable) {
      draggable.classList.remove("dragging");
      const id = draggable.dataset["recordId"];
      data = new FormData();
      data.set("x", parseInt(draggable.style.left));
      data.set("y", parseInt(draggable.style.top));
      await fetch(`/${id}`, {
        method: "POST",
        body: data,
      });
      draggable = null;
    }
  });

  wrapper.addEventListener("dblclick", (e) => {
    const template = document.getElementById("note-template");
    const clone = document.importNode(template.content, true);
    const container = clone.querySelector(".text-container");
    const id = crypto.randomUUID();
    container.dataset["recordId"] = id;
    container.style.left = `${e.pageX}px`;
    container.style.top = `${e.pageY}px`;
    world.appendChild(container);
    setupDraggable(container);
    setupTextInput(container);
  });
}

function setupDraggable(element) {
  element.addEventListener("mousedown", (e) => {
    e.stopPropagation();
    const elementRect = e.target.getBoundingClientRect();
    const nearRightEdge = e.clientX >= elementRect.right - RESIZE_HANDLE_SIZE;
    const nearBottomEdge = e.clientY >= elementRect.bottom - RESIZE_HANDLE_SIZE;
    if (nearRightEdge && nearBottomEdge) return;

    draggable = element;
    element.classList.add("dragging");

    const rect = wrapper.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const elementX = parseFloat(element.style.left);
    const elementY = parseFloat(element.style.top);
    dragOffsetX = (mx - tx) / scale - elementX;
    dragOffsetY = (my - ty) / scale - elementY;
  });

  element.addEventListener(
    "touchstart",
    (e) => {
      if (e.target.closest("textarea")) return;
      e.stopPropagation();
      const elementRect = e.target.getBoundingClientRect();
      const nearRightEdge = e.clientX >= elementRect.right - RESIZE_HANDLE_SIZE;
      const nearBottomEdge =
        e.clientY >= elementRect.bottom - RESIZE_HANDLE_SIZE;
      if (nearRightEdge && nearBottomEdge) return;
      draggable = element;
      element.classList.add("dragging");

      const rect = wrapper.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      const elementX = parseFloat(element.style.left);
      const elementY = parseFloat(element.style.top);

      dragOffsetX = (mx - tx) / scale - elementX;
      dragOffsetY = (my - ty) / scale - elementY;
    },
    { passsive: true },
  );
}

function setupTextInput(element) {
  const id = element.dataset["recordId"];
  const display = element.querySelector(".text-display");

  display.addEventListener("focus", (e) => {
    element.classList.add("unsaved-changes");
  });

  display.addEventListener("blur", (e) => {
    saveContent(id, display);
    element.classList.remove("unsaved-changes");
  });

  display.addEventListener("beforeinput", (e) => {
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    const range = sel.getRangeAt(0);

    let node = range.startContainer;
    let oldSpan = null;
    while (node && node !== display) {
      if (
        node.nodeType === Node.ELEMENT_NODE &&
        node.classList.contains("old")
      ) {
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

    const userSpan = document.createElement("span");
    userSpan.className = "user-edit";
    userSpan.textContent = "";

    const parent = oldSpan.parentNode;
    const oldClass = oldSpan.className;

    if (before) {
      const spanBefore = document.createElement("span");
      spanBefore.className = oldClass;
      spanBefore.textContent = before;
      parent.insertBefore(spanBefore, oldSpan);
    }

    parent.insertBefore(userSpan, oldSpan);

    if (after) {
      const spanAfter = document.createElement("span");
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
      document.execCommand("insertText", false, e.data);
    }
  });

  display.addEventListener("input", () => {
    const sel = window.getSelection();
    const range = sel.rangeCount ? sel.getRangeAt(0) : null;
    Array.from(display.childNodes).forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE && node.textContent.length > 0) {
        const span = document.createElement("span");
        span.className = "new";
        display.insertBefore(span, node);
        span.appendChild(node);
      }
    });

    if (range) {
      sel.removeAllRanges();
      sel.addRange(range);
    }

    debouncedSaveContent(id, display);
  });
}

document.addEventListener("DOMContentLoaded", (e) => {
  setupWorldScroll();
  document.querySelectorAll(".text-container").forEach(function (element) {
    setupDraggable(element);
    setupTextInput(element);
  });
  window.addEventListener("beforeunload", (e) => {
    if (document.querySelector(".unsaved-changes")) e.preventDefault();
  });
});

document.addEventListener("visibilitychange", () => {
  unsavedChanges = document.querySelector(".unsaved-changes");
  if (document.visibilityState == "hidden" && unsavedChanges) {
    const id = unsavedChanges.dataset["recordId"];
    const content = unsavedChanges.querySelector("pre");
    saveContent(id, content);
    unsavedChanges.classList.remove("unsaved-changes");
  }
});
