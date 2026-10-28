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
  panStartTy,
  cameraOpen = 0,
  topZ = 999;
const MIN_SCALE = 0.1,
  MAX_SCALE = 8,
  RESIZE_HANDLE_SIZE = 17,
  FIT_PADDING = 40,
  FIT_MAX_SCALE = 1;

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

function syncTopZ() {
  document.querySelectorAll("#world > .text-container").forEach((el) => {
    const z = parseInt(el.style.zIndex);
    if (z > topZ) topZ = z;
  });
}

async function bringToFront(element) {
  if (parseInt(element.style.zIndex) === topZ) return; // already on top
  const z = ++topZ;
  element.style.zIndex = z;
  const data = new FormData();
  data.set("z", z);
  try {
    await fetch(`/${element.dataset["recordId"]}`, {
      method: "POST",
      body: data,
    });
  } catch (err) {
    console.warn("Couldn't save note z-index", err);
  }
}

function setNoteImage(element, url) {
  const inner = element.querySelector(".text-inner");
  let img = inner.querySelector(".note-image");
  if (!img) {
    img = document.createElement("img");
    img.className = "note-image";
    img.alt = "";
    inner.prepend(img);
  }
  img.src = url;
}

function setupCamera(element) {
  if (element.querySelector(".camera-btn")) return;
  const id = element.dataset["recordId"];

  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "camera-btn";
  btn.title = "Add a photo from your webcam";
  btn.textContent = "📸";
  ["mousedown", "touchstart"].forEach((t) =>
    btn.addEventListener(t, (e) => e.stopPropagation()),
  );
  btn.addEventListener("click", () => openCamera(element, id));
  element.appendChild(btn);
}

async function openCamera(element, id) {
  const inner = element.querySelector(".text-inner");
  if (inner.querySelector(".camera-panel")) return;

  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 } },
      audio: false,
    });
  } catch (err) {
    alert(`Couldn't open the camera: ${err.message}`);
    return;
  }

  cameraOpen++;
  const panel = document.createElement("div");
  panel.className = "camera-panel";
  const video = document.createElement("video");
  video.srcObject = stream;
  video.muted = true;
  video.playsInline = true;
  const snap = document.createElement("button");
  snap.type = "button";
  snap.textContent = "Capture";
  const cancel = document.createElement("button");
  cancel.type = "button";
  cancel.textContent = "Cancel";
  const bar = document.createElement("div");
  bar.className = "camera-bar";
  bar.append(snap, cancel);
  panel.append(video, bar);
  inner.appendChild(panel);
  video.play();

  let closed = false;
  const close = () => {
    if (closed) return;
    closed = true;
    stream.getTracks().forEach((t) => t.stop());
    panel.remove();
    cameraOpen--;
  };
  cancel.addEventListener("click", close);

  snap.addEventListener("click", async () => {
    if (!video.videoWidth) return;
    const MAX_W = 640;
    const ratio = Math.min(1, MAX_W / video.videoWidth);
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(video.videoWidth * ratio);
    canvas.height = Math.round(video.videoHeight * ratio);
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise((res) =>
      canvas.toBlob(res, "image/jpeg", 0.8),
    );
    close();

    const data = new FormData();
    data.set("file", blob, "photo.jpg");
    try {
      const res = await fetch(`/${id}`, { method: "POST", body: data });
      if (!res.ok) throw new Error(res.statusText);
      setNoteImage(element, `/${id}/file?t=${Date.now()}`);
    } catch (err) {
      alert(`Couldn't save the photo: ${err.message}`);
    }
  });
}

function applyTransform() {
  document.getElementById("world").style.transform =
    `translate(${tx}px,${ty}px) scale(${scale})`;
}

function clampScale(s) {
  return Math.min(MAX_SCALE, Math.max(MIN_SCALE, s));
}

function fitToNotes() {
  const notes = document.querySelectorAll("#world > .text-container");
  if (!notes.length) return;

  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;
  notes.forEach((el) => {
    const x = parseFloat(el.style.left) || 0;
    const y = parseFloat(el.style.top) || 0;
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x + el.offsetWidth);
    maxY = Math.max(maxY, y + el.offsetHeight);
  });

  const wrapper = document.getElementById("wrapper");
  const vw = wrapper.clientWidth;
  const vh = wrapper.clientHeight;
  const bw = maxX - minX + FIT_PADDING * 2;
  const bh = maxY - minY + FIT_PADDING * 2;

  scale = Math.min(FIT_MAX_SCALE, clampScale(Math.min(vw / bw, vh / bh)));
  tx = (vw - (maxX - minX) * scale) / 2 - minX * scale;
  ty = (vh - (maxY - minY) * scale) / 2 - minY * scale;
  applyTransform();
}

function setupWorldScroll() {
  const wrapper = document.getElementById("wrapper");

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
}

function setupDraggable(element) {
  element.addEventListener("mousedown", () => bringToFront(element), true);
  element.addEventListener("touchstart", () => bringToFront(element), {
    capture: true,
    passive: true,
  });
  element.addEventListener("focusin", () => bringToFront(element));

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

function setupResize(element) {
  const id = element.dataset["recordId"];
  const sizeKey = () => {
    const w = Math.round(parseFloat(element.style.width));
    const h = Math.round(parseFloat(element.style.height));
    return w && h ? `${w}x${h}` : "";
  };
  element.dataset["lastSize"] = sizeKey(); // size the server already has

  const save = debounce(async () => {
    const key = sizeKey();
    if (!key || key === element.dataset["lastSize"]) return;
    const [w, h] = key.split("x");
    const data = new FormData();
    data.set("w", w);
    data.set("h", h);
    try {
      const res = await fetch(`/${id}`, { method: "POST", body: data });
      if (!res.ok) throw new Error(res.statusText);
      element.dataset["lastSize"] = key;
    } catch (err) {
      console.warn("Couldn't save note size", err);
    }
  }, 500);

  new ResizeObserver(() => {
    const key = sizeKey();
    if (!key || key === element.dataset["lastSize"]) return;
    lastActivity = Date.now();
    save();
  }).observe(element);
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

  function splitOldSpanAtCaret() {
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
    return true;
  }

  function wrapBareTextNodes() {
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
  }

  display.addEventListener("compositionstart", () => {
    splitOldSpanAtCaret();
  });

  display.addEventListener("compositionend", () => {
    wrapBareTextNodes();
    debouncedSaveContent(id, display);
  });

  display.addEventListener("beforeinput", (e) => {
    if (e.isComposing || e.inputType === "insertCompositionText") return;
    if (splitOldSpanAtCaret()) {
      e.preventDefault();
      if (e.data) document.execCommand("insertText", false, e.data);
    }
  });

  display.addEventListener("input", (e) => {
    if (e.isComposing) return;
    wrapBareTextNodes();
    debouncedSaveContent(id, display);
  });
}
async function addNote({ camera = false } = {}) {
  const world = document.getElementById("world");
  const wrapper = document.getElementById("wrapper");
  const template = document.getElementById("note-template");
  const clone = document.importNode(template.content, true);
  const container = clone.querySelector(".text-container");
  const id = crypto.randomUUID();
  container.dataset["recordId"] = id;

  world.appendChild(container);
  const rect = wrapper.getBoundingClientRect();
  const jitter = () => (Math.random() - 0.5) * 40;
  const x =
    (rect.width / 2 - tx) / scale - container.offsetWidth / 2 + jitter();
  const y =
    (rect.height / 2 - ty) / scale - container.offsetHeight / 2 + jitter();
  container.style.left = `${Math.round(x)}px`;
  container.style.top = `${Math.round(y)}px`;
  container.style.zIndex = ++topZ;

  setupDraggable(container);
  setupTextInput(container);
  setupCamera(container);
  setupResize(container);
  if (!camera) container.querySelector(".text-display").focus();

  const data = new FormData();
  data.set("x", Math.round(x));
  data.set("y", Math.round(y));
  data.set("z", topZ);
  data.set("created", Date.now() / 1000);
  await fetch(`/${id}`, { method: "POST", body: data });
  if (camera) openCamera(container, id);
}

document.addEventListener("DOMContentLoaded", (e) => {
  setupWorldScroll();
  fitToNotes();
  document
    .getElementById("add-note")
    .addEventListener("click", () => addNote());
  document
    .getElementById("add-photo-note")
    .addEventListener("click", () => addNote({ camera: true }));
  syncTopZ();
  document.querySelectorAll(".text-container").forEach(function (element) {
    setupDraggable(element);
    setupTextInput(element);
    setupCamera(element);
    setupResize(element);
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

const REFRESH_INTERVAL = 10_000;
const IDLE_BEFORE_REFRESH = 5_000;

let lastActivity = Date.now();
let composing = false;

["keydown", "input", "mousedown", "touchstart", "wheel"].forEach((type) => {
  document.addEventListener(type, () => (lastActivity = Date.now()), {
    capture: true,
    passive: true,
  });
});

document.addEventListener("compositionstart", () => (composing = true), true);
document.addEventListener("compositionend", () => (composing = false), true);

function isBusy() {
  return (
    panning ||
    draggable ||
    composing ||
    cameraOpen > 0 ||
    document.visibilityState === "hidden" ||
    Date.now() - lastActivity < IDLE_BEFORE_REFRESH
  );
}

async function refreshWorld() {
  if (isBusy()) return;

  const focused = document.querySelector(".text-display:focus");
  if (focused) {
    await saveContent(
      focused.closest(".text-container").dataset["recordId"],
      focused,
    );
  }

  try {
    const res = await fetch("/", { cache: "no-store" });
    if (!res.ok) return;
    const doc = new DOMParser().parseFromString(await res.text(), "text/html");

    if (isBusy()) return;

    const world = document.getElementById("world");
    world.replaceChildren(...doc.querySelectorAll("#world > .text-container"));
    syncTopZ();
    world.querySelectorAll(".text-container").forEach((el) => {
      setupDraggable(el);
      setupTextInput(el);
      setupCamera(el);
      setupResize(el);
    });
  } catch (err) {
    console.warn("Refresh failed, will retry", err);
  }
}

setInterval(refreshWorld, REFRESH_INTERVAL);
