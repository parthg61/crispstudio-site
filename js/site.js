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

// Blog index: render posts.json into grey post cards; any posts hide the empty state
const blogList = document.getElementById('blog-list');
if (blogList) {
  fetch('/blog/posts.json', { cache: 'no-cache' })
    .then(r => (r.ok ? r.json() : []))
    .then(posts => {
      if (!Array.isArray(posts) || !posts.length) return;
      const fmt = d => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
      const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
      blogList.innerHTML = [...posts]
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .map(p => `<a class="post" href="${esc(p.url)}"><time datetime="${esc(p.date)}">${fmt(p.date)}</time><h2 class="t-title">${esc(p.title)}</h2><p>${esc(p.excerpt || '')}</p></a>`)
        .join('');
      blogList.hidden = false;
      document.getElementById('blog-empty').hidden = true;
    })
    .catch(() => {});
}

// Contact form: validate, then post to data-endpoint (or fall back to a pre-filled email).
// Entered values are never cleared on failure.
const form = document.getElementById('contact-form');
if (form) {
  const needs = document.getElementById('f-needs');
  const note = document.getElementById('form-note');
  const btn = form.querySelector('button[type=submit]');
  const spinner = form.querySelector('.spinner'); // official curl spinner while the form is sending
  const setErr = (el, msg) => {
    const box = el.closest('.field');
    const out = box.querySelector('.err');
    out.textContent = msg || '';
    out.hidden = !msg;
    (el === needs ? [needs] : [el]).forEach(i => (msg ? i.setAttribute('aria-invalid', 'true') : i.removeAttribute('aria-invalid')));
  };
  const rules = () => {
    const f = form.elements;
    return [
      [f.name, !f.name.value.trim(), 'Tell us your name.'],
      [f.email, !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email.value.trim()), 'Add a valid work email.'],
      [needs, !form.querySelector('[name=need]:checked'), 'Pick at least one.'],
      [f.message, !f.message.value.trim(), 'Tell us a bit about it.'],
    ];
  };
  const check = () => {
    let bad = null;
    rules().forEach(([el, fail, msg]) => { setErr(el, fail ? msg : ''); if (fail && !bad) bad = el; });
    return bad;
  };
  const say = msg => { note.textContent = msg; note.hidden = !msg; };
  form.addEventListener('submit', async e => {
    e.preventDefault();
    say('');
    const bad = check();
    if (bad) { (bad === needs ? needs.querySelector('input') : bad).focus(); return; }
    const d = new FormData(form);
    if (d.get('website')) return; // honeypot
    const list = d.getAll('need').join(', ');
    const endpoint = form.dataset.endpoint;
    if (!endpoint) {
      const body = `Name: ${d.get('name')}\nEmail: ${d.get('email')}\nCompany: ${d.get('company') || '-'}\nNeeds: ${list}\n\n${d.get('message')}`;
      location.href = `mailto:team@crispstudio.in?subject=${encodeURIComponent('Hello from ' + d.get('name'))}&body=${encodeURIComponent(body)}`;
      say('Your email app should open. If it doesn\'t, write to team@crispstudio.in.');
      return;
    }
    btn.disabled = true;
    if (spinner) spinner.hidden = false;
    try {
      d.delete('website');
      d.set('need', list);
      const res = await fetch(endpoint, { method: 'POST', headers: { Accept: 'application/json' }, body: d });
      if (!res.ok) throw new Error(res.status);
      form.hidden = true;
      const done = document.getElementById('form-done');
      done.hidden = false;
      done.focus();
    } catch {
      btn.disabled = false;
      if (spinner) spinner.hidden = true;
      say('That didn\'t go through. Try again, or write to team@crispstudio.in.');
    }
  });
  // Clear a field's error as soon as it is fixed
  const clear = e => {
    const rule = rules().find(([el]) => el === e.target || (el === needs && needs.contains(e.target)));
    if (rule && !rule[1]) setErr(rule[0], '');
  };
  form.addEventListener('input', clear);
  form.addEventListener('change', clear);
}

// Services index chip row (under 1024px): Chrome leaves a partly hidden chip unscrolled on Tab focus,
// so bring the focused chip (and its ring) fully into the row
const svcRow = document.querySelector('.svc-index ul');
if (svcRow) {
  svcRow.addEventListener('focusin', e => {
    if (svcRow.scrollWidth > svcRow.clientWidth) e.target.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  });
}

// Services index: mark the section currently in view (links work without this)
const svcLinks = [...document.querySelectorAll('.svc-index a')];
if (svcLinks.length && 'IntersectionObserver' in window) {
  const byId = new Map(svcLinks.map(a => [a.getAttribute('href').slice(1), a]));
  const visible = new Set();
  const mark = () => {
    const first = [...byId.keys()].find(id => visible.has(id));
    // nothing in the band (hero, closing CTA): clear the highlight instead of leaving the last one on
    svcLinks.forEach(a => (first && a === byId.get(first) ? a.setAttribute('aria-current', 'true') : a.removeAttribute('aria-current')));
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
