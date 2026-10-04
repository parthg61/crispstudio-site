/* Crisp — shared site behaviour */
document.documentElement.classList.add('js');

/* ── CLIENT LOGOS: edit this list ─────────────────────────────
   name = client name, src = logo file (transparent PNG/SVG), h = display height in px */
const LOGOS = [
  { name: 'Kaamna', h: 22, src: '/assets/clients/kaamna.png' },
  { name: 'HDB Financial Services', h: 30, src: '/assets/clients/hdb-financial-services.png' },
  { name: 'SAATH', h: 38, src: '/assets/clients/saath.png' },
  { name: 'The Mind Mojo', h: 38, src: '/assets/clients/the-mind-mojo.png' },
  { name: 'HDFC securities', h: 28, src: '/assets/clients/hdfc-securities.png' },
  { name: 'NMIMS', h: 42, src: '/assets/clients/nmims.png' },
];

// Mobile nav: toggle, close on link click and on Escape
const head = document.querySelector('.site-head');
const toggle = document.querySelector('.nav-toggle');
if (toggle) {
  const setOpen = open => {
    document.body.classList.toggle('nav-open', open);
    toggle.setAttribute('aria-expanded', String(open));
  };
  toggle.addEventListener('click', () => setOpen(!document.body.classList.contains('nav-open')));
  document.querySelectorAll('.nav a').forEach(a => a.addEventListener('click', () => setOpen(false)));
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && document.body.classList.contains('nav-open')) {
      setOpen(false);
      toggle.focus();
    }
  });
}

// Header hairline once the page scrolls
if (head) {
  const onScroll = () => head.classList.toggle('scrolled', window.scrollY > 8);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
}

// Rolling logos (list repeated so the loop is seamless; CSS pauses it for reduced motion)
const track = document.getElementById('track');
if (track) {
  const item = (l, hide) => `<div class="logo"${hide ? ' aria-hidden="true"' : ''}><img src="${l.src}" alt="${hide ? '' : l.name}" style="height:${l.h || 32}px" loading="lazy"></div>`;
  const set = LOGOS.length < 6 ? [...LOGOS, ...LOGOS] : LOGOS;
  track.innerHTML = set.map(l => item(l)).join('') + set.map(l => item(l, true)).join('');
}

// "From the blog": only shown once at least three posts are live
const blogBlock = document.getElementById('from-the-blog');
if (blogBlock) {
  fetch('/blog/posts.json')
    .then(r => (r.ok ? r.json() : []))
    .then(posts => {
      if (!Array.isArray(posts) || posts.length < 3) return;
      const fmt = d => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
      const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
      blogBlock.querySelector('.post-grid').innerHTML = [...posts]
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 3)
        .map(p => `<a class="post" href="${esc(p.url)}"><time datetime="${esc(p.date)}">${fmt(p.date)}</time><h3>${esc(p.title)}</h3><p>${esc(p.excerpt || '')}</p></a>`)
        .join('');
      blogBlock.hidden = false;
    })
    .catch(() => {});
}

// Services index: mark the section currently in view (links work without this)
const svcLinks = [...document.querySelectorAll('.svc-index a')];
if (svcLinks.length && 'IntersectionObserver' in window) {
  const byId = new Map(svcLinks.map(a => [a.getAttribute('href').slice(1), a]));
  const visible = new Set();
  const mark = () => {
    const first = [...byId.keys()].find(id => visible.has(id));
    if (first) svcLinks.forEach(a => (a === byId.get(first) ? a.setAttribute('aria-current', 'true') : a.removeAttribute('aria-current')));
  };
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => (e.isIntersecting ? visible.add(e.target.id) : visible.delete(e.target.id)));
    mark();
  }, { rootMargin: '-30% 0px -60% 0px' });
  byId.forEach((_, id) => { const el = document.getElementById(id); if (el) io.observe(el); });
}

// Work filter: show cases that include the chosen service; the index count follows (zero-padded)
const filters = [...document.querySelectorAll('[data-filter]')];
if (filters.length) {
  const cases = [...document.querySelectorAll('.case[data-services]')];
  const count = document.getElementById('work-count');
  filters.forEach(btn => btn.addEventListener('click', () => {
    const f = btn.dataset.filter;
    filters.forEach(b => b.setAttribute('aria-pressed', String(b === btn)));
    let shown = 0;
    cases.forEach(c => {
      const show = f === 'all' || c.dataset.services.split(' ').includes(f);
      c.hidden = !show;
      if (show) shown++;
    });
    if (count) count.textContent = String(shown).padStart(2, '0');
  }));
}

// Footer year
document.querySelectorAll('[data-year]').forEach(el => (el.textContent = new Date().getFullYear()));
