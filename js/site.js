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

// Mobile nav
const head = document.querySelector('.site-head');
const toggle = document.querySelector('.nav-toggle');
if (toggle) {
  toggle.addEventListener('click', () => {
    const open = document.body.classList.toggle('nav-open');
    toggle.setAttribute('aria-expanded', open);
  });
  document.querySelectorAll('.nav a').forEach(a => a.addEventListener('click', () => {
    document.body.classList.remove('nav-open');
    toggle.setAttribute('aria-expanded', 'false');
  }));
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && document.body.classList.contains('nav-open')) toggle.click();
  });
}

// Header border once the page scrolls
if (head) {
  const onScroll = () => head.classList.toggle('scrolled', window.scrollY > 8);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
}

// Rolling logos (list repeated so the loop is seamless)
const track = document.getElementById('track');
if (track) {
  const item = (l, hide) => `<div class="logo"${hide ? ' aria-hidden="true"' : ''}><img src="${l.src}" alt="${hide ? '' : l.name}" style="height:${l.h || 32}px" loading="lazy"></div>`;
  const set = LOGOS.length < 6 ? [...LOGOS, ...LOGOS] : LOGOS;
  track.innerHTML = set.map(l => item(l)).join('') + set.map(l => item(l, true)).join('');
}

// "From the blog" — only shown once at least three posts are live
const blogBlock = document.getElementById('from-the-blog');
if (blogBlock) {
  fetch('/blog/posts.json')
    .then(r => (r.ok ? r.json() : []))
    .then(posts => {
      if (!Array.isArray(posts) || posts.length < 3) return;
      const fmt = d => new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
      const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
      blogBlock.querySelector('.post-grid').innerHTML = posts
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 3)
        .map(p => `<a class="post" href="${esc(p.url)}"><time datetime="${esc(p.date)}">${fmt(p.date)}</time><h3>${esc(p.title)}</h3><p>${esc(p.excerpt || '')}</p></a>`)
        .join('');
      blogBlock.hidden = false;
    })
    .catch(() => {});
}

// Reveal on scroll
const reveals = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver(entries => entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }), { rootMargin: '0px 0px -8% 0px' });
  reveals.forEach(el => io.observe(el));
} else {
  reveals.forEach(el => el.classList.add('in'));
}

// Footer year
document.querySelectorAll('[data-year]').forEach(el => (el.textContent = new Date().getFullYear()));
