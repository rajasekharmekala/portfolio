(() => {
  'use strict';
  const report = document.querySelector('main.report');
  if (!report) return;
  const headings = [...report.querySelectorAll('h2')];
  const sidebar = document.querySelector('.desk-contents');
  const list = sidebar.querySelector('ol');
  const picker = document.querySelector('#desk-section');
  const links = new Map();
  headings.forEach((heading, index) => {
    if (!heading.id) {
      if (heading.parentElement.id) heading.id = `${heading.parentElement.id}-heading`;
      else heading.id = `chapter-${index + 1}`;
      while (document.querySelectorAll(`[id="${CSS.escape(heading.id)}"]`).length > 1) heading.id += '-section';
    }
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = `#${encodeURIComponent(heading.id)}`;
    link.textContent = heading.textContent.trim();
    item.append(link);
    list.append(item);
    links.set(heading.id, link);
    picker.add(new Option(link.textContent, heading.id));
  });
  if (headings.length) {
    sidebar.hidden = false;
    picker.hidden = false;
  }
  picker.addEventListener('change', () => {
    const heading = document.getElementById(picker.value);
    if (!heading) return;
    heading.scrollIntoView({block: 'start'});
    heading.tabIndex = -1;
    heading.focus({preventScroll: true});
    history.replaceState(null, '', `#${encodeURIComponent(heading.id)}`);
  });
  report.querySelectorAll('table:not(.infobox)').forEach(table => {
    let wrapper = table.parentElement;
    if (!wrapper.classList.contains('table-wrap')) {
      wrapper = document.createElement('div');
      wrapper.className = 'table-wrap';
      table.before(wrapper);
      wrapper.append(table);
    }
    wrapper.tabIndex = 0;
    wrapper.setAttribute('role', 'region');
    wrapper.setAttribute('aria-label', table.caption?.textContent.trim() || 'Research data table');
  });
  const print = document.querySelector('#desk-print');
  print.hidden = false;
  print.addEventListener('click', () => window.print());
  const progress = document.querySelector('.desk-progress');
  progress.hidden = false;
  let scheduled = false;
  const update = () => {
    scheduled = false;
    const distance = document.documentElement.scrollHeight - innerHeight;
    progress.value = distance > 0 ? Math.max(0, Math.min(100, scrollY / distance * 100)) : 100;
    let active = headings[0];
    for (const heading of headings) {
      if (heading.getBoundingClientRect().top > 140) break;
      active = heading;
    }
    links.forEach((link, identifier) => {
      if (identifier === active?.id) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    if (active) picker.value = active.id;
  };
  const schedule = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(update);
  };
  addEventListener('scroll', schedule, {passive: true});
  addEventListener('resize', schedule);
  addEventListener('load', schedule, {once: true});
  update();
})();
