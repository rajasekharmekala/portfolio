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

  // Interactive Audiobook / Narrative Reader Bar (activates on *_book.html pages)
  const audioBar = document.querySelector('.book-audio-bar');
  if (audioBar && 'speechSynthesis' in window) {
    const playBtn = audioBar.querySelector('[data-audio-action="play"]');
    const prevBtn = audioBar.querySelector('[data-audio-action="prev"]');
    const nextBtn = audioBar.querySelector('[data-audio-action="next"]');
    const stopBtn = audioBar.querySelector('[data-audio-action="stop"]');
    const rateSel = audioBar.querySelector('[data-audio-rate]');
    const statusEl = audioBar.querySelector('[data-audio-status]');
    const paragraphs = [...report.querySelectorAll('.book-chapter p')];
    let idx = 0;
    let playing = false;

    const clearHighlight = () => paragraphs.forEach(p => p.classList.remove('is-speaking'));
    const speakCurrent = () => {
      if (!playing || idx < 0 || idx >= paragraphs.length) {
        playing = false;
        clearHighlight();
        if (playBtn) playBtn.textContent = 'Play Audiobook';
        if (statusEl) statusEl.textContent = 'Ready to listen';
        return;
      }
      speechSynthesis.cancel();
      clearHighlight();
      const para = paragraphs[idx];
      para.classList.add('is-speaking');
      para.scrollIntoView({block: 'center', behavior: 'smooth'});
      const sec = para.closest('.book-chapter');
      const chTitle = sec?.querySelector('h2')?.textContent.trim() || 'Book';
      if (statusEl) statusEl.textContent = `Reading (${idx + 1}/${paragraphs.length}) • ${chTitle.slice(0, 48)}`;
      const utter = new SpeechSynthesisUtterance(para.textContent.trim());
      utter.rate = parseFloat(rateSel?.value || '1.0') || 1.0;
      utter.onend = () => {
        if (!playing) return;
        idx += 1;
        speakCurrent();
      };
      speechSynthesis.speak(utter);
    };

    playBtn?.addEventListener('click', () => {
      if (playing) {
        playing = false;
        speechSynthesis.cancel();
        playBtn.textContent = 'Resume Audiobook';
        if (statusEl) statusEl.textContent = `Paused at paragraph ${idx + 1}/${paragraphs.length}`;
      } else {
        playing = true;
        playBtn.textContent = 'Pause';
        speakCurrent();
      }
    });
    prevBtn?.addEventListener('click', () => {
      idx = Math.max(0, idx - 1);
      if (playing) speakCurrent();
    });
    nextBtn?.addEventListener('click', () => {
      idx = Math.min(paragraphs.length - 1, idx + 1);
      if (playing) speakCurrent();
    });
    stopBtn?.addEventListener('click', () => {
      playing = false;
      idx = 0;
      speechSynthesis.cancel();
      clearHighlight();
      if (playBtn) playBtn.textContent = 'Play Audiobook';
      if (statusEl) statusEl.textContent = 'Ready to listen';
    });
    rateSel?.addEventListener('change', () => {
      if (playing) speakCurrent();
    });
  }
})();
