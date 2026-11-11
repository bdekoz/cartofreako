'use strict';
(() => {
  const sequence = window.OBSERVER_SEQUENCE;
  const frames = sequence.frames;
  const $ = id => document.getElementById(id);
  let index = 0;
  let playing = false;
  let timer = null;
  let generation = 0;
  const previews = new Map();

  function preload(i) {
    if (i < 0 || i >= frames.length) return Promise.resolve();
    if (!previews.has(i)) {
      previews.set(i, new Promise(resolve => {
        const image = new Image();
        image.onload = image.onerror = () => resolve();
        image.src = frames[i].preview;
      }));
    }
    return previews.get(i);
  }

  function stop() {
    playing = false;
    clearTimeout(timer);
    timer = null;
    $('play').textContent = index === frames.length - 1 ? 'Replay' : 'Play';
    $('play').setAttribute('aria-pressed', 'false');
  }

  function layers() {
    $('plate').classList.toggle('hide-names', !$('names').checked);
    $('plate').classList.toggle('show-previous', $('previous-horizon').checked && index > 0);
    $('plate').style.width = $('zoom').value + '%';
    $('previous-horizon').disabled = index === 0;
  }

  async function show(next, announce = true) {
    const ticket = ++generation;
    const chosen = Math.max(0, Math.min(frames.length - 1, next));
    await preload(chosen);
    if (ticket !== generation) return;
    index = chosen;
    const frame = frames[index];
    // Parse as SVG/XML: HTML fragment parsing loses alternate namespace
    // prefixes on xlink:href, leaving valid <use> instances visibly empty.
    const markup = $('view').value === 'orientation' ? frame.orientation_svg : frame.full_svg;
    const parsed = new DOMParser().parseFromString(markup, 'image/svg+xml');
    if (parsed.querySelector('parsererror')) throw new Error('The archived SVG could not be parsed');
    $('plate').replaceChildren(document.importNode(parsed.documentElement, true));
    layers();
    $('local-time').textContent = frame.pacific_label;
    $('utc-time').textContent = frame.timestamp.replace('T', ' ').replace('Z', ' UTC');
    $('hour').textContent = String(index).padStart(2, '0') + ' / ' + String(frames.length - 1).padStart(2, '0');
    $('slider').value = index;
    $('slider').setAttribute('aria-valuetext', 'Hour ' + index + ', ' + frame.pacific_label);
    $('plotted').textContent = frame.plotted.toLocaleString();
    $('excluded').textContent = frame.epoch_exclusions;
    $('failures').textContent = frame.propagation_failures;
    $('sidereal').textContent = frame.sidereal_degrees.toFixed(3) + '°';
    $('map-pdf').href = frame.map_pdf;
    $('legend-pdf').href = frame.legend_pdf;
    $('map-svg').href = frame.map;
    $('previous').disabled = index === 0;
    $('next').disabled = index === frames.length - 1;
    document.documentElement.dataset.hour = String(index);
    if (announce) $('status').textContent = index === 0 ? 'Accepted starting plate. Manual stepping is ready.' :
      index === frames.length - 1 ? 'Final hourly state. Replay explicitly returns to the starting instant.' :
      'Hour ' + index + '. ' + frame.plotted.toLocaleString() + ' objects above the horizon.';
    preload(index + 1);
    if (!playing) $('play').textContent = index === frames.length - 1 ? 'Replay' : 'Play';
  }

  function queue() {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      if (!playing) return;
      if (index >= frames.length - 1) { stop(); return; }
      await show(index + 1);
      if (playing) queue();
    }, sequence.seconds_per_plate * 1000);
  }

  $('previous').addEventListener('click', () => { stop(); show(index - 1); });
  $('next').addEventListener('click', () => { stop(); show(index + 1); });
  $('reset').addEventListener('click', () => { stop(); show(0); });
  $('slider').addEventListener('input', () => { stop(); show(Number($('slider').value)); });
  $('play').addEventListener('click', async () => {
    if (playing) { stop(); return; }
    if (index === frames.length - 1) await show(0);
    playing = true;
    $('play').textContent = 'Pause';
    $('play').setAttribute('aria-pressed', 'true');
    queue();
  });
  $('view').addEventListener('change', () => show(index, false));
  for (const id of ['names', 'previous-horizon', 'zoom']) $(id).addEventListener('change', layers);
  document.addEventListener('keydown', event => {
    if (event.target.matches('input,select,textarea')) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault(); stop(); show(index + (event.key === 'ArrowRight' ? 1 : -1));
    }
  });
  $('slider').max = frames.length - 1;
  $('study-title').textContent = frames.length === 24 ? 'One observer. Twenty-four skies.' : 'One observer. Twenty-five skies.';
  $('sample-count').textContent = frames.length;
  $('elapsed-hours').textContent = frames.length - 1;
  $('video').href = sequence.video;
  $('video').textContent = (frames.length * sequence.seconds_per_plate) + '-second MKV';
  document.fonts.ready.then(async () => {
    await show(0);
    document.documentElement.dataset.ready = 'true';
  });
})();
