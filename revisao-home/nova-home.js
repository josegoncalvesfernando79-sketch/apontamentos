// Destaque simples de navegação por seção para revisão da UX.
const links = [...document.querySelectorAll('.menu a[href^="#"]')];
const sections = links.map(l => document.querySelector(l.getAttribute('href'))).filter(Boolean);
const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (!e.isIntersecting) return;
    const id = `#${e.target.id}`;
    links.forEach((l) => l.classList.toggle('active', l.getAttribute('href') === id));
  });
}, { threshold: 0.6 });
sections.forEach((s) => io.observe(s));
