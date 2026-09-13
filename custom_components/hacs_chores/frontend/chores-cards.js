/* HACS Chores 0.2.1 — native custom elements, no CDN or build step. */
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const color = value => /^#[0-9a-f]{6}$/i.test(value) ? value : '#538b78';
const priority = ['', 'Niedrig', 'Normal', 'Hoch', 'Dringend'];
const css = `
 :host {
    display: block;
    color: var(--primary-text-color, #233e34);
    font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
}
 * {
    box-sizing: border-box;
}
ha-card {
    display: block;
    border-radius: 24px;
    overflow: hidden;
    background: var(--ha-card-background, var(--card-background-color, #fafaf6));
    border: 1px solid var(--divider-color, #e1e7df);
}
 .wrap {
    padding: 24px;
}
.eyebrow {
    text-transform: uppercase;
    letter-spacing: 2px;
    font-size: 10px;
    font-weight: 750;
    color: var(--secondary-text-color, #6c7e73);
}
 header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    margin: 8px 0 22px;
}
h2 {
    margin: 0;
    font-size: 27px;
    letter-spacing: -.7px;
    font-weight: 650;
}
h3 {
    margin: 0;
    font-size: 17px;
    line-height: 1.35;
    overflow-wrap: anywhere;
}
 p {
    line-height: 1.55;
}
.muted {
    color: var(--secondary-text-color, #6c7e73);
}
.subtitle {
    font-size: 13px;
    margin: 7px 0 0;
}
.counter {
    flex-shrink: 0;
    border-radius: 16px;
    padding: 10px 14px;
    text-align: center;
    background: var(--secondary-background-color, #eef2e9);
}
.counter strong {
    font-size: 25px;
    display: block;
}
.counter small {
    font-size: 11px;
}
 button, select {
    font: inherit;
    color: inherit;
}
button {
    cursor: pointer;
}
button:disabled {
    cursor: default;
}
button:focus-visible, select:focus-visible {
    outline: 3px solid var(--primary-color, #43755e);
    outline-offset: 3px;
}
.filters {
    display: flex;
    gap: 8px;
    margin-bottom: 18px;
    flex-wrap: wrap;
}
 select, .plain {
    background: var(--card-background-color, #fafaf6);
    border: 1px solid var(--divider-color, #dce4da);
    border-radius: 10px;
    padding: 9px 12px;
}
.plain {
    font-size: 13px;
}
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 215px), 1fr));
    grid-auto-rows: 8px;
    gap: 12px;
    align-items: start;
}
 .cell {
    min-width: 0;
}
.tile {
    display: block;
    width: 100%;
    text-align: left;
    border: 1px solid var(--divider-color, #dce4da);
    border-radius: 17px;
    padding: 18px;
    background: var(--card-background-color, #fff);
    transition: background .2s, border-color .2s;
    position: relative;
    overflow: hidden;
}
.tile.due {
    border-top: 3px solid #64896b;
}
.tile.urgent {
    border-top-color: #bd714c;
}
.tile.future {
    opacity: .8;
}
.tile:hover {
    border-color: var(--primary-color, #43755e);
}
 .category {
    font-size: 10px;
    font-weight: 750;
    text-transform: uppercase;
    letter-spacing: 1.3px;
    margin-bottom: 12px;
    color: var(--secondary-text-color, #6c7e73);
}
.description {
    font-size: 13px;
    white-space: pre-wrap;
    margin: 10px 0 15px;
    overflow-wrap: anywhere;
}
.tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin: 12px 0;
}
.tag {
    font-size: 10px;
    border-radius: 7px;
    padding: 4px 7px;
    background: var(--secondary-background-color, #f0f3ec);
}
.tag.high {
    color: #aa512e;
    background: #f8e9df;
}
.date {
    font-size: 12px;
    font-weight: 650;
    margin-top: 14px;
}
.last {
    font-size: 11px;
    margin-top: 7px;
    line-height: 1.4;
}
.done-label {
    color: #417251;
    font-size: 12px;
    margin-top: 10px;
}
 .empty {
    padding: 22px 0;
    line-height: 1.6;
}
.notice {
    font-size: 12px;
    line-height: 1.6;
    margin-top: 18px;
    color: var(--secondary-text-color, #6c7e73);
}
.toast {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    border-radius: 12px;
    background: var(--secondary-background-color, #edf3e8);
    padding: 12px 14px;
    margin-top: 15px;
    font-size: 13px;
}
.error {
    color: var(--error-color, #b43b33);
    font-size: 13px;
    line-height: 1.5;
}
 .tile.celebrate {
    animation: done .85s ease both;
    border-color: #528a62;
}
.check {
    font-size: 30px;
    color: #528a62;
    float: right;
    margin: 0 0 8px 8px;
}
@keyframes done {
    0% {
    transform: scale(1);
}
35% {
    transform: scale(.95);
    background: #e1efdb;
}
70% {
    transform: scale(1.025);
}
100% {
    transform: scale(1);
}
}
 dialog {
    color: var(--primary-text-color, #233e34);
    background: var(--ha-card-background, var(--card-background-color, #fafaf6));
    border: 1px solid var(--divider-color, #dce4da);
    border-radius: 24px;
    padding: 26px;
    width: min(440px, calc(100vw - 28px));
    max-height: 85vh;
    overflow: auto;
    box-shadow: 0 24px 100px #0004;
}
dialog::backdrop {
    background: #14271f80;
    backdrop-filter: blur(3px);
}
.dialog-head {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: start;
    margin-bottom: 12px;
}
.close {
    background: none;
    border: 0;
    font-size: 24px;
    padding: 0 4px;
}
.members {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-top: 18px;
}
.member {
    display: flex;
    align-items: center;
    gap: 10px;
    text-align: left;
    padding: 12px;
    border-radius: 13px;
    border: 1px solid var(--divider-color, #dce4da);
    background: var(--secondary-background-color, #f2f4ee);
    overflow-wrap: anywhere;
}
.avatar {
    display: grid;
    place-items: center;
    width: 35px;
    height: 35px;
    flex: 0 0 35px;
    border-radius: 50%;
    color: #fff;
    background: var(--member-color, #538b78);
    font-size: 13px;
    font-weight: 750;
    text-shadow: 0 1px 2px #0008;
}
 .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 245px), 1fr));
    gap: 14px;
}
.person {
    border: 1px solid var(--divider-color, #dce4da);
    border-radius: 17px;
    padding: 18px;
    min-width: 0;
}
.person-head {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 18px;
}
.person-head strong {
    overflow-wrap: anywhere;
}
.amount {
    font-size: 29px;
    letter-spacing: -.7px;
}
.amount small {
    font-size: 13px;
    letter-spacing: 0;
}
.stat-sub {
    font-size: 12px;
    margin: 6px 0 12px;
}
.bar {
    height: 7px;
    border-radius: 10px;
    background: var(--secondary-background-color, #edf0e8);
    overflow: hidden;
}
.bar span {
    height: 100%;
    display: block;
    background: var(--member-color, #538b78);
    border-radius: 10px;
}
.task-list {
    list-style: none;
    margin: 15px 0 0;
    padding: 0;
}
.task-list li {
    display: flex;
    gap: 12px;
    justify-content: space-between;
    padding: 9px 0;
    border-top: 1px solid var(--divider-color, #e5e9e0);
    font-size: 12px;
}
.task-list li span:first-child {
    overflow-wrap: anywhere;
}
.task-list li span:last-child {
    white-space: nowrap;
    font-weight: 650;
}
:host(hacs-chores-quick-card) {
  height: 100%;
  min-height: 70px;
  container-type: size;
  contain-intrinsic-block-size: 70px;
}

:host(hacs-chores-quick-card) ha-card {
  height: 100%;
  border-radius: var(--ha-card-border-radius, 12px);
  border: var(--ha-card-border-width, 1px) solid
    var(--ha-card-border-color, var(--divider-color, #e1e7df));
  box-shadow: var(--ha-card-box-shadow, none);
}

/* Im inaktiven Zustand die gesamte Karte abdunkeln. */
:host(hacs-chores-quick-card)
  ha-card:has(.quick-card.disabled) {
  opacity: 0.5;
}

:host(hacs-chores-quick-card) .wrap {
  height: 100%;
  padding: 0;
}

:host(hacs-chores-quick-card) .wrap > .eyebrow:first-child {
  padding: 18px 18px 0;
}

:host(hacs-chores-quick-card) .wrap > p {
  margin-left: 18px;
  margin-right: 18px;
}

.quick-card {
  height: 100%;
  min-height: 0;
  position: relative;
  display: grid;
  grid-template-columns: minmax(180px, 0.8fr) minmax(0, 2fr);
  gap: 12px;
  align-items: stretch;
  padding: 8px 12px;
  cursor: pointer;
}

.quick-card:focus-visible {
  outline: 3px solid var(--primary-color, #43755e);
  outline-offset: -3px;
}

.quick-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  padding: 0 6px;
  text-align: left;
}

/* Icon ohne farbige Hintergrundfläche. */
.quick-icon {
  display: grid;
  place-items: center;
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  border-radius: 0;
  background: transparent;
  color: var(--primary-text-color, #233e34);
}

.quick-icon ha-icon {
  --mdc-icon-size: 28px;
}

.quick-copy {
  flex: 1;
  min-width: 0;
}

.quick-copy .eyebrow {
  margin-bottom: 3px;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-size: 10px;
  font-weight: 750;
  color: var(--secondary-text-color, #6c7e73);
  opacity: 0.7;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-title {
  font-size: 17px;
  font-weight: 650;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-title-short {
  display: none;
}

.quick-arrow {
  margin-left: auto;
  color: var(--secondary-text-color, #6c7e73);
  font-size: 23px;
}

.quick-tasks {
  display: flex;
  gap: 8px;
  min-width: 0;
  min-height: 0;
  overflow-x: auto;
  scrollbar-width: thin;
}

.quick-task {
  min-width: min(155px, 65vw);
  flex: 1 0 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: left;
  border: 1px solid var(--divider-color, #dce4da);
  border-radius: 14px;
  padding: 10px 12px;
  background: var(--secondary-background-color, #f0f3ec);
  overflow: hidden;
}

.quick-task:hover {
  border-color: var(--primary-color, #43755e);
}

.quick-task .category {
  margin: 0 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-task strong {
  font-size: 13px;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-task small {
  display: none;
  color: var(--secondary-text-color, #6c7e73);
  margin-top: 5px;
  white-space: nowrap;
}

/* Responsive Darstellung bei offenen Aufgaben. */
@container (max-width: 420px) and (max-height: 124px) {
  .quick-title-full {
    display: none;
  }

  .quick-title-short {
    display: inline;
  }
}

@container (min-height: 125px) {
  .quick-card {
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(0, 1fr);
    gap: 6px;
  }

  .quick-summary {
    padding: 0 6px;
  }

  .quick-icon {
    width: 38px;
    height: 38px;
    flex-basis: 38px;
  }

  .quick-task {
    justify-content: flex-start;
    min-width: min(170px, 72vw);
    padding: 12px;
  }

  .quick-task strong {
    white-space: normal;
  }

  .quick-task small {
    display: block;
  }
}

/* Inaktiver Zustand: linksbündig und vertikal zentriert.
   Diese Regeln stehen bewusst nach den Container-Regeln. */
.quick-card.disabled {
  cursor: default;
  opacity: 1;
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: minmax(0, 1fr);
}

.quick-card.disabled .quick-summary {
  justify-self: stretch;
  align-self: stretch;
}

.quick-card.disabled .quick-icon {
  width: 42px;
  height: 42px;
  flex-basis: 42px;
}

.quick-card.disabled .quick-arrow {
  display: none;
}

.quick-card.disabled .quick-title-full {
  display: inline;
}

.quick-card.disabled .quick-title-short {
  display: none;
}
`;

class ChoresBase extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:'open'});
    this.shadowRoot.innerHTML = `<style>${css}</style><ha-card><div class="wrap" id="body"></div></ha-card><dialog></dialog>`;
    this._generation = 0;
    this._config = {};
    this._dialog = this.shadowRoot.querySelector('dialog');
    this._dialog.addEventListener('click', event => { if (event.target === this._dialog) this._dialog.close(); });
  }
  setConfig(config) { this._config = {...config}; this.render(); }
  set hass(value) {
    const changed = this._hass?.connection !== value.connection;
    this._hass = value;
    if (changed) this.stop();
    this.connect();
  }
  connectedCallback() { this.connect(); this.render(); }
  disconnectedCallback() {
    this.stop();
    this._resize?.disconnect();
    clearTimeout(this._doneTimer);
    this._pending = null;
    this._celebrate = null;
    this._dialog.close();
  }
  stop() {
    this._generation++;
    this._unsubscribe?.();
    this._unsubscribe = null;
    this._connecting = false;
    clearTimeout(this._retry);
  }
  async connect() {
    if (!this.isConnected || !this._hass || this._connecting || this._unsubscribe) return;
    this._connecting = true;
    const generation = this._generation;
    try {
      const unsubscribe = await this._hass.connection.subscribeMessage(data => {
        if (generation !== this._generation) return;
        this._data = data;
        this._error = null;
        this.render();
      }, {type:'hacs_chores/subscribe'});
      if (generation !== this._generation || !this.isConnected) { unsubscribe(); return; }
      this._unsubscribe = unsubscribe;
    } catch (error) {
      if (generation !== this._generation) return;
      this._error = error.message || 'Verbindung fehlgeschlagen.';
      this.render();
      this._retry = setTimeout(() => this.connect(), 5000);
    } finally {
      if (generation === this._generation) this._connecting = false;
    }
  }
  getCardSize() { return 6; }
  getGridOptions() { return {columns:12, min_columns:6, rows:'auto'}; }
  date(value) {
    if (!value) return 'Noch nie';
    return new Intl.DateTimeFormat('de-DE', {timeZone:this._data?.timezone || 'Europe/Berlin', day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}).format(new Date(value));
  }
  body(html) { this.shadowRoot.getElementById('body').innerHTML = html; }
  ready() {
    if (!this._data?.available) {
      this.body(`<div class="eyebrow">HACS Chores</div><p>${this._error ? esc(this._error) : 'Haushalt wird geladen …'}</p><p class="notice">Integration unter Einstellungen → Geräte & Dienste hinzufügen.</p>`);
      return false;
    }
    return true;
  }
  openTask(task) {
    if (!task) return;
    const members = this._data.members.filter(m => m.active);
    this._dialog.innerHTML = `<div class="dialog-head"><div><div class="category">${esc(task.category)}</div><h3 id="dialog-title">${esc(task.title)}</h3></div><button class="close" aria-label="Schließen">×</button></div>
      <p class="description">${esc(task.description)}</p><p class="subtitle muted">${task.effort_minutes} Minuten · ${this.date(task.due_at)}</p>
      ${task.is_due?`<p>Wer hat die Aufgabe erledigt?</p><div class="members">${members.map(m => `<button class="member" data-member="${esc(m.id)}"><span class="avatar" style="--member-color:${color(m.color)}">${esc(m.name.slice(0,2).toUpperCase())}</span><span>${esc(m.name)}</span></button>`).join('')}</div>${!members.length?'<p>Lege zuerst ein aktives Mitglied in den Einstellungen der Integration an.</p>':''}`:'<p>Diese Aufgabe ist noch nicht fällig.</p>'}<p class="error" id="dialog-error" role="alert"></p>`;
    this._dialog.setAttribute('aria-labelledby','dialog-title');
    this._dialog.querySelector('.close').addEventListener('click', () => this._dialog.close());
    this._dialog.querySelectorAll('[data-member]').forEach(button => button.addEventListener('click', () => this.complete(task, button.dataset.member)));
    this._dialog.showModal();
  }
  async complete(task, memberId) {
    if (this._pending) return;
    this._pending = {...task};
    this._actionError = null;
    const dialog = this._dialog;
    dialog.querySelectorAll('[data-member]').forEach(b => {b.disabled = true;});
    try {
      const result = await this._hass.callWS({type:'hacs_chores/complete',task_id:task.id,member_id:memberId,due_at:task.due_at});
      dialog.close();
      this._celebrate = task.id;
      this._undo = result.completion_id;
      this.render();
      clearTimeout(this._doneTimer);
      this._doneTimer = setTimeout(() => {this._pending=null;this._celebrate=null;this.render();}, 1200);
    } catch (error) {
      this._pending = null;
      const message = error.message || 'Speichern fehlgeschlagen. Bitte erneut versuchen.';
      dialog.querySelector('#dialog-error').textContent = message;
      dialog.querySelectorAll('[data-member]').forEach(b => {b.disabled = false;});
      this._actionError = message;
      this.render();
    }
  }
}

class ChoresOverviewCard extends ChoresBase {
  static getStubConfig() { return {title:'Unser Haushalt'}; }
  render() {
    if (!this.ready()) return;
    const focusTask = this.shadowRoot.activeElement?.dataset?.task;
    const tasks = this._data.tasks.filter(t => t.enabled);
    const selected = this._category || this._config.category || '';
    let shown = tasks.filter(t => (!selected || t.category === selected) && (!this._config.due_only || t.is_due || this._pending?.id === t.id));
    if (this._pending) shown = shown.map(t => t.id === this._pending.id ? this._pending : t);
    shown.sort((a,b) => a.due_at.localeCompare(b.due_at) || b.priority-a.priority || a.title.localeCompare(b.title, 'de') || a.id.localeCompare(b.id));
    const count = tasks.filter(t => t.is_due).length;
    const categories = [...new Set(tasks.map(t => t.category))].sort((a,b) => a.localeCompare(b,'de'));
    this.body(`<div class="eyebrow">Gemeinsam zu Hause</div><header><div><h2>${esc(this._config.title || 'Unser Haushalt')}</h2><p class="subtitle muted">Kleine Aufgaben. Gemeinsam erledigt.</p></div><div class="counter"><strong>${count}</strong><small>jetzt fällig</small></div></header>
      <div class="filters"><select aria-label="Kategorie"><option value="">Alle Kategorien</option>${categories.map(c => `<option value="${esc(c)}" ${c===selected?'selected':''}>${esc(c)}</option>`).join('')}</select></div>
      <div class="grid">${shown.map(t => this.tile(t)).join('')}</div>
      ${!shown.length ? '<div class="empty">Hier ist gerade nichts offen.<br><span class="muted">Aufgaben lassen sich in den Einstellungen der Integration anlegen.</span></div>' : ''}
      <div id="status" role="status">${this._undo ? `<div class="toast"><span>Aufgabe erledigt ✓</span><button class="plain" id="undo">Rückgängig</button></div>` : ''}</div>
      ${this._actionError ? `<p class="error" role="alert">${esc(this._actionError)}</p>` : ''}
      <div class="notice">Nach Fälligkeit sortiert, bei gleichem Termin nach Priorität.</div>`);
    this.shadowRoot.querySelector('select').addEventListener('change', event => { this._category = event.target.value; this._config.category = ''; this.render(); });
    this.shadowRoot.querySelectorAll('[data-task]').forEach(button => button.addEventListener('click', () => {
      if (this._pending) return;
      this.openTask(tasks.find(t => t.id === button.dataset.task));
    }));
    this.shadowRoot.getElementById('undo')?.addEventListener('click', () => this.undo());
    this.masonry();
    if (focusTask) [...this.shadowRoot.querySelectorAll('[data-task]')].find(b => b.dataset.task === focusTask)?.focus({preventScroll:true});
  }
  tile(task) {
    const done = this._celebrate === task.id;
    return `<div class="cell"><button class="tile ${task.is_due?'due':'future'} ${task.priority>=3?'urgent':''} ${done?'celebrate':''}" data-task="${esc(task.id)}" ${this._pending?.id===task.id?'aria-busy="true"':''}>
      ${done?'<span class="check" aria-hidden="true">✓</span>':''}<div class="category">${esc(task.category)}</div><h3>${esc(task.title)}</h3>
      ${task.description?`<p class="description muted">${esc(task.description)}</p>`:''}
      <div class="tags"><span class="tag ${task.priority>=3?'high':''}">${priority[task.priority]}</span><span class="tag">${task.effort_minutes} Min.</span></div>
      <div class="date">${done?'Erledigt ✓':`${task.is_due?'Fällig':'Nächster Termin'} · ${this.date(task.due_at)}`}</div>
      ${task.last_done?`<div class="last muted">Zuletzt ${esc(task.last_member_name)} · ${this.date(task.last_done)}</div>`:''}
      ${!task.is_due && task.last_done?'<div class="done-label">Für diesen Durchgang erledigt ✓</div>':''}
    </button></div>`;
  }
  masonry() {
    this._resize?.disconnect();
    const size = tile => { tile.parentElement.style.gridRowEnd = `span ${Math.ceil((tile.getBoundingClientRect().height+12)/20)}`; };
    this._resize = new ResizeObserver(entries => entries.forEach(entry => size(entry.target)));
    this.shadowRoot.querySelectorAll('.tile').forEach(tile => { size(tile); this._resize.observe(tile); });
  }
  async undo() {
    const completionId = this._undo;
    this.shadowRoot.getElementById('undo').disabled = true;
    try {
      await this._hass.callWS({type:'hacs_chores/undo',completion_id:completionId});
      clearTimeout(this._doneTimer);
      this._undo = null; this._pending = null; this._celebrate = null; this._actionError = null;
    } catch (error) { this._actionError = error.message || 'Rückgängig fehlgeschlagen.'; }
    this.render();
  }
}

class ChoresStatsCard extends ChoresBase {
  static getStubConfig() { return {title:'Unser Einsatz'}; }
  render() {
    if (!this.ready()) return;
    const people = this._data.statistics.filter(p => p.active || p.count);
    const total = this._data.total_minutes;
    this.body(`<div class="eyebrow">Die letzten 14 Tage</div><header><div><h2>${esc(this._config.title || 'Unser Einsatz')}</h2><p class="subtitle muted">Jeder Handgriff zählt.</p></div><div class="counter"><strong>${total}</strong><small>Minuten gesamt</small></div></header>
      <div class="stats">${people.map(person => `<section class="person" style="--member-color:${color(person.color)}"><div class="person-head"><span class="avatar">${esc(person.name.slice(0,2).toUpperCase())}</span><strong>${esc(person.name)}${!person.active?' (inaktiv)':''}</strong></div>
      <div class="amount">${person.minutes} <small>Minuten</small></div><div class="stat-sub muted">${person.count} erledigt · ${person.share.toLocaleString('de-DE')} % des Aufwands</div>
      <div class="bar" role="meter" aria-label="Anteil am Aufwand" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${person.share}"><span style="width:${Math.min(100,Math.max(0,person.share))}%"></span></div>
      <ul class="task-list">${person.tasks.map(t => `<li><span>${esc(t.title)}</span><span>${t.count} ×</span></li>`).join('')}</ul>${!person.count?'<p class="subtitle muted">Noch keine Erledigungen in diesem Zeitraum.</p>':''}</section>`).join('')}</div>
      ${!people.length?'<p class="empty">Lege Haushaltsmitglieder in den Einstellungen der Integration an.</p>':''}
      <p class="notice">Aufwand = hinterlegte Minuten pro erledigter Aufgabe. Keine Zeitmessung.<br>${this.date(this._data.window_start)} bis ${this.date(this._data.now)}</p>`);
  }
}

class ChoresQuickCard extends ChoresBase {
  static getStubConfig() { return {title:'Aufgaben',navigation_path:'/lovelace/chores',max_tasks:3}; }
  getCardSize() { return 2; }
  getGridOptions() { return {columns:12,min_columns:6,rows:2,min_rows:1,max_rows:4}; }
  render() {
    if (!this.ready()) return;
    const limitValue = Number(this._config.max_tasks ?? 3);
    const limit = Number.isFinite(limitValue) ? Math.min(20,Math.max(1,Math.trunc(limitValue))) : 3;
    const tasks = this._data.tasks
      .filter(task => task.enabled && task.is_due)
      .sort((a,b) => a.due_at.localeCompare(b.due_at) || b.priority-a.priority || a.title.localeCompare(b.title,'de') || a.id.localeCompare(b.id))
      .slice(0,limit);
    const count = this._data.tasks.filter(task => task.enabled && task.is_due).length;
    const title = this._config.title || 'Aufgaben';
    const disabled = count === 0;
    const countLabel = disabled ? 'Alles erledigt' : `${count} ${count === 1 ? 'Aufgabe' : 'Aufgaben'} offen`;
    const navLabel = `${title}: ${countLabel}${disabled ? '' : '. Zur Aufgabenansicht'}`;
    this.body(`<div class="quick-card ${disabled?'disabled':''}" role="button" ${disabled?'aria-disabled="true"':'tabindex="0"'} aria-label="${esc(navLabel)}">
      <div class="quick-summary"><span class="quick-icon"><ha-icon icon="${disabled?'mdi:check-all':'mdi:format-list-checks'}"></ha-icon></span><div class="quick-copy"><div class="eyebrow">${esc(title)}</div><div class="quick-title"><span class="quick-title-full">${countLabel}</span><span class="quick-title-short">${disabled?'Erledigt':`${count} offen`}</span></div></div><span class="quick-arrow" aria-hidden="true">›</span></div>
      ${tasks.length ? `<div class="quick-tasks">${tasks.map(task => `<button class="quick-task" data-task="${esc(task.id)}" aria-label="${esc(task.title)} erledigen"><span class="category">${esc(task.category)}</span><strong>${esc(task.title)}</strong><small>Fällig · ${this.date(task.due_at)}</small></button>`).join('')}</div>` : ''}
    </div>`);
    const card = this.shadowRoot.querySelector('.quick-card');
    card.addEventListener('click', event => {
      const taskButton = event.target.closest('[data-task]');
      if (taskButton) {
        this.openTask(tasks.find(task => task.id === taskButton.dataset.task));
        return;
      }
      if (!disabled) this.navigate();
    });
    card.addEventListener('keydown', event => {
      if (event.target !== card || disabled || (event.key !== 'Enter' && event.key !== ' ')) return;
      event.preventDefault();
      this.navigate();
    });
  }
  navigate() {
    const path = typeof this._config.navigation_path === 'string' && this._config.navigation_path.trim() ? this._config.navigation_path.trim() : '/lovelace/chores';
    history.pushState(null,'',path);
    window.dispatchEvent(new CustomEvent('location-changed'));
  }
}

if (!customElements.get('hacs-chores-card')) customElements.define('hacs-chores-card', ChoresOverviewCard);
if (!customElements.get('hacs-chores-stats-card')) customElements.define('hacs-chores-stats-card', ChoresStatsCard);
if (!customElements.get('hacs-chores-quick-card')) customElements.define('hacs-chores-quick-card', ChoresQuickCard);
window.customCards = window.customCards || [];
for (const entry of [
  {type:'hacs-chores-card',name:'HACS Chores – Aufgaben',description:'Wiederkehrende Aufgaben mit Mitgliederauswahl',preview:true},
  {type:'hacs-chores-stats-card',name:'HACS Chores – Statistik',description:'Aufwand und häufigste Aufgaben der letzten 14 Tage',preview:true},
  {type:'hacs-chores-quick-card',name:'HACS Chores – Kompakt',description:'Fällige Aufgaben und Navigation auf kleinem Raum',preview:true},
]) if (!window.customCards.some(card => card.type === entry.type)) window.customCards.push(entry);
