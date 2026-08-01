/* Shared behaviour for every page on voxellabs.ai — nav state, scroll reveal,
   and video facades. Loaded on every route, so it assumes nothing exists. */

/* sticky nav background once you leave the top */
const nav = document.getElementById('nav');
if (nav) {
  const onScroll = () => nav.classList.toggle('stuck', window.scrollY > 24);
  onScroll();
  window.addEventListener('scroll', onScroll, {passive:true});
}

/* reveal-on-scroll for anything marked .rv */
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  });
}, {threshold:.06, rootMargin:'0px 0px -50px 0px'});
document.querySelectorAll('.rv').forEach(el => io.observe(el));

/* Video facades — a poster that swaps itself for the real player on click.
   Six embedded iframes would cost more to load than the rest of the site put
   together, so nothing from Vimeo is fetched until someone actually presses play.

   Delegated from the document rather than bound per element: the projects index
   injects its rows from a script that runs after this file, so anything bound at
   load time would miss every tile on the page it matters most on. */
document.addEventListener('click', (ev) => {
  const el = ev.target.closest('[data-vimeo]');
  if (!el || el.classList.contains('playing')) return;
  ev.preventDefault();
  const f = document.createElement('iframe');
  f.src = 'https://player.vimeo.com/video/' + el.dataset.vimeo +
          '?autoplay=1&title=0&byline=0&portrait=0';
  f.allow = 'autoplay; fullscreen; picture-in-picture';
  f.setAttribute('allowfullscreen', '');
  f.title = el.dataset.title || 'Video';
  el.replaceChildren(f);
  el.classList.add('playing');
});
