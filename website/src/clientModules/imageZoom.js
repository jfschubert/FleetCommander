// Click-to-zoom for screenshots: images in docs pages and images marked with data-zoom on other pages
// open full-size in an overlay; a click, Esc or scrolling closes it.
import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';

const SELECTOR = '.markdown img, img[data-zoom]';

function close() {
  const overlay = document.querySelector('.fc-zoom');
  if (!overlay) return;
  overlay.classList.remove('open');
  document.removeEventListener('keydown', onKey);
  window.removeEventListener('scroll', close);
  setTimeout(() => overlay.remove(), 200);
}
function onKey(ev) {
  if (ev.key === 'Escape') close();
}
function open(img) {
  close();
  const overlay = document.createElement('div');
  overlay.className = 'fc-zoom';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-label', img.alt || 'Image');
  const big = document.createElement('img');
  big.src = img.currentSrc || img.src;
  big.alt = img.alt;
  overlay.appendChild(big);
  if (img.alt) {
    const cap = document.createElement('div');
    cap.className = 'fc-zoom-caption';
    cap.textContent = img.alt;
    overlay.appendChild(cap);
  }
  overlay.addEventListener('click', close);
  document.body.appendChild(overlay);
  requestAnimationFrame(() => overlay.classList.add('open'));
  document.addEventListener('keydown', onKey);
  window.addEventListener('scroll', close, {passive: true, once: true});
}

if (ExecutionEnvironment.canUseDOM) {
  document.addEventListener('click', (ev) => {
    const img = ev.target.closest?.(SELECTOR);
    if (!img || img.closest('a')) return;   // linked images keep their link
    ev.preventDefault();
    open(img);
  });
}

export function onRouteDidUpdate() {
  close();
}
