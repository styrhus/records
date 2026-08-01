(function () {
  var btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'scroll-to-top';
  btn.setAttribute('aria-label', 'Scroll to top');
  btn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';
  document.body.appendChild(btn);

  var isSingle = !!document.querySelector('main.mode-single');

  // Reveal the button once the opening viewport has scrolled out of sight.
  var ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      btn.classList.toggle('visible', window.scrollY > window.innerHeight);
      ticking = false;
    });
  });

  // The last chapter summary at or above the viewport top is the one we're inside.
  function currentChapterSummary() {
    var summaries = document.querySelectorAll('details.chapter > summary');
    var found = null;
    for (var i = 0; i < summaries.length; i++) {
      if (summaries[i].getBoundingClientRect().top < 2) found = summaries[i];
      else break;
    }
    return found;
  }

  btn.addEventListener('click', function () {
    // Single mode: first click lands on the current chapter, next click goes to the top.
    if (isSingle) {
      var summary = currentChapterSummary();
      if (summary && summary.getBoundingClientRect().top < -2) {
        summary.scrollIntoView({ behavior: 'smooth' });
        return;
      }
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // A "#" click on a chapter summary links to it without toggling the fold.
  var chapterAnchors = document.querySelectorAll('details.chapter > summary .anchor');
  for (var j = 0; j < chapterAnchors.length; j++) {
    chapterAnchors[j].addEventListener('click', function (e) { e.stopPropagation(); });
  }

  // Open any collapsed <details> that holds the hash target so TOC/anchor links reveal it.
  function revealHashTarget() {
    if (!location.hash) return;
    var t = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!t) return;
    var el = t.parentElement, opened = false;
    while (el) {
      if (el.tagName === 'DETAILS' && !el.open) { el.open = true; opened = true; }
      el = el.parentElement;
    }
    if (opened) t.scrollIntoView();
  }
  window.addEventListener('hashchange', revealHashTarget);
  if (location.hash) revealHashTarget();

  // Load the Spotify embed on first open, so it measures the real panel size (a hidden load renders compact).
  var spotify = document.querySelector('details.spotify');
  if (spotify) spotify.addEventListener('toggle', function () {
    var f = spotify.querySelector('iframe[data-src]');
    if (spotify.open && f) { f.src = f.getAttribute('data-src'); f.removeAttribute('data-src'); }
  });

  // Close the open TOC / Spotify / filter panel when clicking outside it.
  var poppers = document.querySelectorAll('details.toc, details.spotify, details.filter');
  for (var k = 0; k < poppers.length; k++) {
    (function (d) {
      document.addEventListener('click', function (e) {
        if (d.open && !d.contains(e.target)) d.open = false;
      });
    })(poppers[k]);
  }

  // Record filter (single mode): hide non-matching cards, state synced with the URL query string.
  var filter = document.querySelector('details.filter');
  if (filter) {
    function splitCSV(s) { return s ? s.split(',').filter(Boolean) : []; }

    function readState() {
      var q = new URLSearchParams(location.search);
      return {
        tags: splitCSV(q.get('tags')),
        langs: splitCSV(q.get('language')),
        from: q.get('from') || '',
        to: q.get('to') || '',
        word: q.get('word') || ''
      };
    }

    function stateFromForm() {
      var st = { tags: [], langs: [], from: '', to: '', word: '' };
      filter.querySelectorAll('input:checked[name="tags"]').forEach(function (i) { st.tags.push(i.value); });
      filter.querySelectorAll('input:checked[name="language"]').forEach(function (i) { st.langs.push(i.value); });
      var from = filter.querySelector('input[name="from"]');
      var to = filter.querySelector('input[name="to"]');
      var word = filter.querySelector('input[name="word"]');
      st.from = from ? from.value : '';
      st.to = to ? to.value : '';
      st.word = word ? word.value : '';
      return st;
    }

    function prefill(st) {
      filter.querySelectorAll('input[name="tags"]').forEach(function (i) { i.checked = st.tags.indexOf(i.value) !== -1; });
      filter.querySelectorAll('input[name="language"]').forEach(function (i) { i.checked = st.langs.indexOf(i.value) !== -1; });
      var from = filter.querySelector('input[name="from"]');
      var to = filter.querySelector('input[name="to"]');
      var word = filter.querySelector('input[name="word"]');
      if (from) from.value = st.from;
      if (to) to.value = st.to;
      if (word) word.value = st.word;
    }

    // Hand-built query string keeps the commas literal.
    function writeURL(st) {
      var parts = [];
      if (st.tags.length) parts.push('tags=' + st.tags.map(encodeURIComponent).join(','));
      if (st.langs.length) parts.push('language=' + st.langs.map(encodeURIComponent).join(','));
      if (st.from) parts.push('from=' + st.from);
      if (st.to) parts.push('to=' + st.to);
      if (st.word) parts.push('word=' + encodeURIComponent(st.word));
      var qs = parts.join('&');
      history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash);
    }

    function applyFilter(st) {
      var active = !!(st.tags.length || st.langs.length || st.from || st.to || st.word);
      // Word input compiles as a case-insensitive regex; invalid syntax falls back to literal text.
      var wordRe = null;
      if (st.word) {
        try { wordRe = new RegExp(st.word, 'i'); }
        catch (e) { wordRe = new RegExp(st.word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i'); }
      }
      // [data-date] skips the metadata-less _index intro card.
      document.querySelectorAll('main.mode-single article.record-page[data-date]').forEach(function (card) {
        var show = true;
        if (st.tags.length) {
          var cardTags = splitCSV(card.getAttribute('data-tags'));
          show = st.tags.some(function (t) { return cardTags.indexOf(t) !== -1; });
        }
        if (show && st.langs.length) show = st.langs.indexOf(card.getAttribute('lang') || 'none') !== -1;
        if (show && st.from) show = card.dataset.date >= st.from;
        if (show && st.to) show = card.dataset.date <= st.to;
        if (show && wordRe) {
          // Whole visible card text, whitespace-collapsed, cached once — cards never change.
          if (card.wordText === undefined) card.wordText = card.textContent.replace(/\s+/g, ' ');
          show = wordRe.test(card.wordText);
        }
        card.classList.toggle('filter-hidden', active && !show);
      });
      document.querySelectorAll('details.chapter').forEach(function (ch) {
        var hasMatch = !!ch.querySelector('article.record-page:not(.filter-hidden)');
        ch.classList.toggle('filter-hidden', active && !hasMatch);
        if (active && hasMatch) {
          // Force-open so matches aren't hidden in a collapsed fold; remember the pre-filter state once.
          if (!('filterOpen' in ch.dataset)) ch.dataset.filterOpen = ch.open ? '1' : '0';
          ch.open = true;
        } else if (!active && 'filterOpen' in ch.dataset) {
          ch.open = ch.dataset.filterOpen === '1';
          delete ch.dataset.filterOpen;
        }
      });
      highlightWord(wordRe);
    }

    // Tint word matches in visible cards (Custom Highlight API; browsers without it just filter).
    function highlightWord(re) {
      if (typeof Highlight === 'undefined' || !CSS.highlights) return;
      if (!re) { CSS.highlights.delete('word-match'); return; }
      var g = new RegExp(re.source, 'gi');
      var hl = new Highlight();
      var any = false;
      document.querySelectorAll('main.mode-single article.record-page[data-date]:not(.filter-hidden)').forEach(function (card) {
        var walk = document.createTreeWalker(card, NodeFilter.SHOW_TEXT);
        for (var node = walk.nextNode(); node; node = walk.nextNode()) {
          g.lastIndex = 0;
          for (var m = g.exec(node.data); m; m = g.exec(node.data)) {
            if (m[0]) {
              var r = document.createRange();
              r.setStart(node, m.index);
              r.setEnd(node, m.index + m[0].length);
              hl.add(r);
              any = true;
            }
            // Zero-length match: step forward so exec can't loop in place.
            if (m.index === g.lastIndex) g.lastIndex++;
          }
        }
      });
      if (any) CSS.highlights.set('word-match', hl); else CSS.highlights.delete('word-match');
    }

    function onFilterChange() {
      var st = stateFromForm();
      writeURL(st);
      applyFilter(st);
    }
    filter.addEventListener('change', onFilterChange);
    // The word input filters live per keystroke; change alone would fire only on blur/Enter.
    var wordInput = filter.querySelector('input[name="word"]');
    if (wordInput) wordInput.addEventListener('input', onFilterChange);

    var clear = filter.querySelector('.filter-clear');
    if (clear) clear.addEventListener('click', function () {
      filter.querySelectorAll('input[type="checkbox"]').forEach(function (i) { i.checked = false; });
      filter.querySelectorAll('input[type="date"], input[type="search"]').forEach(function (i) { i.value = ''; });
      writeURL(stateFromForm());
      applyFilter(stateFromForm());
    });

    var initial = readState();
    prefill(initial);
    applyFilter(initial);
  }
})();
