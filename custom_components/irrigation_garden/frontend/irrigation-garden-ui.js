/* Irrigation Garden UI: searchable mappings and local appearance, original engine unchanged. */
(() => {
  'use strict';
  const VERSION = '0.4.0b1';
  const decisionFallback = {"title": "Why this watering decision?", "empty": "No decisions recorded yet. Entries appear at the next attempt.", "missing": "Decision journal is not loaded. Update the engine packages.", "history": "Decision history", "cycle": "Cycle", "zone": "Zone", "base": "Base time", "selected": "Selected time", "rain": "Rainfall adjustment", "temperature": "Temperature adjustment", "minimum": "Raised to the minimum time", "maximum": "Limited to the maximum time", "testing": "Testing mode: minutes become seconds", "simulation": "Outputs blocked — simulation", "snapshot_mismatch": "Engine time differs from the saved settings. The selected time is authoritative; an exact cause cannot be confirmed.", "factor_unknown": "Adjustment multiplier unavailable; the engine uses zero", "hint": "Recorded decisions, not a forecast or proof of water flow. Weather changes do not rewrite these entries. The latest 64 entries are retained.", "master_off": "Skipped: master control is off", "cycle_busy": "Skipped: another cycle is active", "schedule_disabled": "Skipped: this schedule is disabled", "raining_now": "Skipped: the rain sensor reports rain", "rain_unknown": "Skipped: the rain sensor does not confirm dry conditions", "settings_unknown": "Skipped: required settings are unavailable", "waiting_for_entity": "Waiting for the configured entity state", "wait_timeout": "Skipped: waiting for the entity timed out", "start_conditions_changed": "Skipped: start conditions changed while waiting", "cycle_started": "Cycle accepted for processing", "cycle_finished": "Cycle processing finished", "cycle_stopped": "Cycle interrupted by STOP or a safety shutdown", "duration_unknown": "Skipped: duration data is unavailable", "duration_zero": "Skipped: base time is zero", "zone_not_today": "Skipped: this zone is not scheduled today", "rain_adjusted_zero": "Skipped: rainfall adjustment reduced time to zero", "temp_adjusted_zero": "Skipped: temperature adjustment reduced time to zero", "duration_rounded_zero": "Skipped: the engine selected zero seconds", "output_unassigned": "Skipped: no valid switch is assigned", "duration_selected": "Watering time selected", "duration_snapshot_changed": "The engine selected a time using different inputs", "output_unavailable": "Interrupted: the assigned output is unavailable", "output_permission_changed": "Interrupted: permission to open the valve changed", "output_not_on": "Interrupted: the output did not confirm opening", "output_not_off": "Interrupted: the output did not confirm closing", "unknown": "Unrecognized decision"};
  const decisionPolish = {"title": "Dlaczego tak podlewa?", "empty": "Nie zapisano jeszcze decyzji. Wpisy pojawią się przy następnej próbie.", "missing": "Dziennik decyzji nie jest wczytany. Zaktualizuj pakiety silnika.", "history": "Historia decyzji", "cycle": "Cykl", "zone": "Strefa", "base": "Czas bazowy", "selected": "Wybrany czas", "rain": "Korekta opadów", "temperature": "Korekta temperatury", "minimum": "Podniesiono do minimalnego czasu", "maximum": "Ograniczono do maksymalnego czasu", "testing": "Tryb testowy: minuty zamieniono na sekundy", "simulation": "Wyjścia zablokowane — symulacja", "snapshot_mismatch": "Czas silnika różni się od zapisanych ustawień. Obowiązuje wybrany czas; nie można potwierdzić dokładnej przyczyny.", "factor_unknown": "Brak mnożnika korekty; silnik przyjmuje zero", "hint": "Zapisane decyzje, bez prognozowania ani potwierdzania przepływu wody. Zmiana pogody nie zmienia wpisów. Zachowywane są ostatnie 64 wpisy.", "master_off": "Pominięto: sterowanie główne jest wyłączone", "cycle_busy": "Pominięto: trwa już cykl podlewania", "schedule_disabled": "Pominięto: ten harmonogram jest wyłączony", "raining_now": "Pominięto: czujnik zgłasza deszcz", "rain_unknown": "Pominięto: czujnik deszczu nie potwierdza, że jest sucho", "settings_unknown": "Pominięto: wymagane ustawienia są niedostępne", "waiting_for_entity": "Oczekiwanie na ustawiony stan encji", "wait_timeout": "Pominięto: upłynął czas oczekiwania na encję", "start_conditions_changed": "Pominięto: warunki startu zmieniły się podczas oczekiwania", "cycle_started": "Przyjęto cykl do wykonania", "cycle_finished": "Zakończono wykonywanie cyklu", "cycle_stopped": "Cykl przerwany przez STOP lub zabezpieczenie", "duration_unknown": "Pominięto: czas podlewania jest niedostępny", "duration_zero": "Pominięto: czas bazowy wynosi zero", "zone_not_today": "Pominięto: strefa nie jest zaplanowana na dziś", "rain_adjusted_zero": "Pominięto: korekta opadów obniżyła czas do zera", "temp_adjusted_zero": "Pominięto: korekta temperatury obniżyła czas do zera", "duration_rounded_zero": "Pominięto: silnik wybrał zero sekund", "output_unassigned": "Pominięto: nie przypisano prawidłowego zaworu", "duration_selected": "Wybrano czas podlewania", "duration_snapshot_changed": "Silnik wybrał czas na podstawie innych danych", "output_unavailable": "Przerwano: przypisane wyjście jest niedostępne", "output_permission_changed": "Przerwano: zmieniło się zezwolenie na otwarcie zaworu", "output_not_on": "Przerwano: wyjście nie potwierdziło otwarcia", "output_not_off": "Przerwano: wyjście nie potwierdziło zamknięcia", "unknown": "Nierozpoznana decyzja"};
  const EVENT = 'irrigation-garden-appearance';
  const memory = new Map();
  const palette = {
    light: {'primary-background-color':'#f4f6f8','secondary-background-color':'#ffffff','card-background-color':'#ffffff','ha-card-background':'#ffffff','primary-text-color':'#17212b','secondary-text-color':'#52606d','disabled-text-color':'#677684','divider-color':'#c5cdd4','ha-card-border-color':'#c5cdd4','accent-color':'#00796b','primary-color':'#00796b','state-icon-color':'#52606d','paper-item-icon-color':'#52606d','input-fill-color':'#edf1f4','input-ink-color':'#17212b','input-label-ink-color':'#52606d','mdc-theme-surface':'#ffffff','mdc-theme-on-surface':'#17212b','error-color':'#b3261e'},
    dark: {'primary-background-color':'#111827','secondary-background-color':'#1f2937','card-background-color':'#1f2937','ha-card-background':'#1f2937','primary-text-color':'#f3f4f6','secondary-text-color':'#cbd5e1','disabled-text-color':'#a5b1c2','divider-color':'#526176','ha-card-border-color':'#526176','accent-color':'#80cbc4','primary-color':'#80cbc4','state-icon-color':'#cbd5e1','paper-item-icon-color':'#cbd5e1','input-fill-color':'#273449','input-ink-color':'#f3f4f6','input-label-ink-color':'#cbd5e1','mdc-theme-surface':'#1f2937','mdc-theme-on-surface':'#f3f4f6','error-color':'#ffb4ab'}
  };
  const fallback = {"search":"Search entities","save":"Save","cancel":"Cancel","clear":"Clear selection","none":"Not configured","empty":"No matching entities","unavailable":"Unavailable","invalid":"Select an existing compatible entity.","failed":"Save failed. Your previous setting is retained.","busy":"Stop watering and close mapped valves before changing valve assignments.","changed":"This setting changed elsewhere. Reopen the picker before saving.","more":"matching entities — type to narrow the list","dark":"Dark mode","light":"Light mode","to_dark":"Switch to dark mode","to_light":"Switch to light mode","loading":"Loading…","load_failed":"Cannot load the original card. Refresh the dashboard.","measurement":"Measurement","forecast":"Forecast","condition":"Current conditions","healthy":"Available; value is valid","missing_source":"Assigned entity does not exist","missing_helper":"Mapping helper is unavailable","unknown_value":"Source has no known value","wrong_unit":"Wrong unit; expected","wrong_domain":"Wrong entity type; expected","invalid_value":"Invalid value","value":"Value","reported":"Last report to HA","updated":"State or attributes updated","checked":"Report time checked","refresh":"Refresh report time","report_failed":"Report time unavailable; retry refresh","no_report":"No report timestamp","report_hint":"An unchanged value does not indicate failure. HA report time is not the time of a physical measurement or forecast issue.","raining_on":"on = raining; off = dry. Check the sensor polarity."};
  const polishFallback = {"search":"Szukaj encji","save":"Zapisz","cancel":"Anuluj","clear":"Wyczyść wybór","none":"Nie skonfigurowano","empty":"Brak pasujących encji","unavailable":"Niedostępna","invalid":"Wybierz istniejącą encję odpowiedniego typu.","failed":"Zapis nie powiódł się. Poprzednie ustawienie zostało zachowane.","busy":"Przed zmianą przypisania zaworu zatrzymaj podlewanie i zamknij przypisane zawory.","changed":"To ustawienie zmieniono w innym miejscu. Otwórz wybór ponownie przed zapisaniem.","more":"pasujących encji — wpisz tekst, aby zawęzić listę","dark":"Tryb ciemny","light":"Tryb jasny","to_dark":"Przełącz na tryb ciemny","to_light":"Przełącz na tryb jasny","loading":"Wczytywanie…","load_failed":"Nie można wczytać oryginalnej karty. Odśwież panel.","measurement":"Pomiar","forecast":"Prognoza","condition":"Bieżąca pogoda","healthy":"Dostępna; wartość poprawna","missing_source":"Przypisana encja nie istnieje","missing_helper":"Pomocnik przypisania jest niedostępny","unknown_value":"Źródło nie ma znanej wartości","wrong_unit":"Niewłaściwa jednostka; wymagana","wrong_domain":"Niewłaściwy typ encji; wymagany","invalid_value":"Nieprawidłowa wartość","value":"Wartość","reported":"Ostatni raport do HA","updated":"Zmiana wartości lub atrybutów","checked":"Czas raportu sprawdzono","refresh":"Odśwież czas raportu","report_failed":"Czas raportu niedostępny; ponów odświeżanie","no_report":"Brak czasu raportu","report_hint":"Niezmienna wartość nie oznacza awarii. Czas raportu do HA nie jest czasem pomiaru fizycznego ani wydania prognozy.","raining_on":"on = pada; off = sucho. Sprawdź polaryzację czujnika."};
  const labels = c => ({...fallback,...(c?.ui_labels?.save==='Zapisz'?polishFallback:{}),...c?.ui_labels});
  const key = h => `irrigation-garden:appearance:${h?.user?.id || 'local'}`;
  function mode(h) {
    const k=key(h); let value=memory.get(k);
    try {value=localStorage.getItem(k)||value;} catch {}
    return value==='dark'||value==='light' ? value : (h?.themes?.darkMode ? 'dark':'light');
  }
  function paint(el,h) {
    const value=mode(h);el.dataset.igMode=value;
    for(const [name,color] of Object.entries(palette[value]))el.style.setProperty('--'+name,color);
    el.style.colorScheme=value;
    return value;
  }
  function parent(el) {return el.parentElement || el.getRootNode()?.host;}
  function ancestor(el,tag) {for(let p=parent(el);p;p=parent(p))if(p.localName===tag)return p;}
  function focusedWithin(root){let active=root.ownerDocument.activeElement;while(active?.shadowRoot){const next=active.shadowRoot.activeElement;if(!next)break;active=next;}return active?.getRootNode()===root?active:null;}
  const commonCSS = `:host{display:block;color:var(--primary-text-color);font-family:var(--paper-font-body1_-_font-family,system-ui,sans-serif)}button,input{font:inherit;color:inherit}button{cursor:pointer;min-height:44px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);padding:8px 12px}button:focus-visible,input:focus-visible{outline:3px solid var(--accent-color);outline-offset:2px}button:disabled{opacity:.55;cursor:default}[hidden]{display:none!important}`;
  class ThemedCard extends HTMLElement {
    constructor(){super();this.attachShadow({mode:'open'});this.shadowRoot.innerHTML=`<style>${commonCSS}</style><div id="body"></div>`;this._appearance=()=>this._update();}
    setConfig(c){if(!c.card || c.card.type==='custom:irrigation-garden-themed-card')throw Error('An original card is required');this._config=c;this._generation=(this._generation||0)+1;this._child=undefined;this._pending=false;this.shadowRoot.getElementById('body').replaceChildren();this._update();}
    set hass(h){this._hass=h;this._update();}
    connectedCallback(){window.addEventListener(EVENT,this._appearance);this._update();}
    disconnectedCallback(){window.removeEventListener(EVENT,this._appearance);}
    _update(){
      if(!this._hass||!this._config)return;
      const m=paint(this,this._hass);
      if(this._child){this._child.hass={...this._hass,themes:{...this._hass.themes,darkMode:m==='dark'}};return;}
      if(this._pending)return;
      this._pending=true;const generation=this._generation;const body=this.shadowRoot.getElementById('body');body.textContent=labels(this._config).loading;
      Promise.resolve().then(()=>window.loadCardHelpers()).then(helpers=>{
        if(generation!==this._generation)return;
        this._child=helpers.createCardElement(this._config.card);body.replaceChildren(this._child);this._update();
      }).catch(()=>{if(generation===this._generation){body.textContent=labels(this._config).load_failed;this._pending=false;}});
    }
    getCardSize(){return this._child?.getCardSize?.()??1;}
    getGridOptions(){return this._child?.getGridOptions?.()??{columns:12,rows:'auto'};}
  }
  class AppearanceButton extends HTMLElement {
    constructor(){super();this.attachShadow({mode:'open'});this.shadowRoot.innerHTML=`<style>${commonCSS}.bar{display:flex;justify-content:flex-end;padding:2px 0 6px}button{display:flex;align-items:center;gap:8px}.icon{font-size:22px;line-height:1}</style><div class="bar"><button type="button"><span class="icon" aria-hidden="true"></span><span id="label"></span></button></div>`;this.shadowRoot.querySelector('button').addEventListener('click',()=>this._toggle());this._appearance=()=>this._update();this._prior=null;}
    setConfig(c){this._config=c;this._update();}
    set hass(h){this._hass=h;this._update();}
    connectedCallback(){window.addEventListener(EVENT,this._appearance);this._update();}
    disconnectedCallback(){window.removeEventListener(EVENT,this._appearance);if(this._view&&this._prior){for(const [p,[v,priority,owned]] of this._prior){if(this._view.style.getPropertyValue(p)===owned){if(v)this._view.style.setProperty(p,v,priority);else this._view.style.removeProperty(p);}}}this._prior=null;this._view=null;}
    _update(){
      if(!this._hass)return;const m=paint(this,this._hass);const t=labels(this._config);const dark=m==='dark';const b=this.shadowRoot.querySelector('button');b.setAttribute('aria-label',dark?t.to_light:t.to_dark);b.setAttribute('aria-pressed',String(dark));b.title=b.getAttribute('aria-label');this.shadowRoot.querySelector('.icon').textContent=dark?'☀':'☾';this.shadowRoot.getElementById('label').textContent=dark?t.dark:t.light;
      if(this._config?.show_decisions!==false){if(!this._journal){this._journal=document.createElement('irrigation-garden-decisions');this._journal.setConfig({ui_labels:t.save==='Zapisz'?decisionPolish:decisionFallback});this.shadowRoot.append(this._journal);}this._journal.hass=this._hass;}else if(this._journal){this._journal.remove();this._journal=null;}
      if(!this.isConnected)return;
      const view=ancestor(this,'hui-view');if(!view)return;
      if(!this._prior){this._view=view;this._prior=new Map();for(const p of ['--primary-background-color','--lovelace-background'])this._prior.set(p,[view.style.getPropertyValue(p),view.style.getPropertyPriority(p),'']);}
      for(const [p,entry]of this._prior){entry[2]=palette[m]['primary-background-color'];view.style.setProperty(p,entry[2]);}
    }
    _toggle(){const value=mode(this._hass)==='dark'?'light':'dark';const k=key(this._hass);memory.set(k,value);try{localStorage.setItem(k,value);}catch{}window.dispatchEvent(new CustomEvent(EVENT,{detail:{key:k,mode:value}}));}
    getCardSize(){return 1;}
    getGridOptions(){return{columns:12,rows:'auto'};}
  }
  function watering(h){
    for(const id of ['script.irrigation_run_a_cycle','script.irrigation_run_a_single_zone_on_demand',...Array.from({length:3},(_,i)=>`input_boolean.irrigation_cycle${i+1}_running`)]){const s=h.states[id];if(s&&!['off','idle'].includes(s.state))return true;}
    for(let n=1;n<=16;n++){const id=h.states[`input_text.irrigation_zone${n}_switch_entity_id`]?.state;if(id&&h.states[id]?.state==='on')return true;}
    return false;
  }
  function accepts(s,c){return !!s && (c.domains.includes('*') || c.domains.includes(s.entity_id.split('.')[0])) && (!c.units || c.units.includes(s.attributes?.unit_of_measurement));}
  function weatherKind(entity){const prefix='input_text.irrigation_external_sensor_';if(!entity.startsWith(prefix))return undefined;const suffix=entity.slice(prefix.length);if(suffix.startsWith('forecast_'))return 'forecast';if(suffix==='weather_outlook')return 'condition';if(suffix.startsWith('rainfall_')||['raining_now','current_temp'].includes(suffix))return 'measurement';}
  // One read-only template request for all visible weather rows, at most once
  // per minute per connection (or on explicit refresh). No state_reported firehose.
  const reports = new WeakMap();
  const REPORT_EVENT = 'irrigation-garden-reports';
  const REPORT_TEMPLATE = `{% set ns=namespace(rows=[]) %}{% for h in states.input_text if h.entity_id.startswith('input_text.irrigation_external_sensor_') %}{% set s=states[h.state] if h.state is match('^[a-z_]+[.][a-z0-9_]+$') else none %}{% set ns.rows=ns.rows+[{'helper':h.entity_id,'source':h.state,'last_reported':s.last_reported.isoformat() if s else none,'last_updated':s.last_updated.isoformat() if s else none}] %}{% endfor %}{{ ns.rows|to_json }}`;
  function reportCache(h){const owner=h?.connection||h?.callApi;if(!owner || !['object','function'].includes(typeof owner))return null;if(!reports.has(owner))reports.set(owner,{rows:[],checked:0,pending:null,error:false});return reports.get(owner);}
  function loadReports(h,force=false){
    const cache=reportCache(h);if(!cache||!h.callApi)return;
    if(cache.pending||(!force&&Date.now()-cache.checked<60000))return;
    cache.checked=Date.now();cache.error=false;
    cache.pending=Promise.resolve().then(()=>h.callApi('POST','template',{template:REPORT_TEMPLATE})).then(body=>{
      const rows=typeof body==='string'?JSON.parse(body):body;
      if(!Array.isArray(rows))throw Error('Invalid report response');
      cache.rows=rows.filter(r=>r&&typeof r.helper==='string'&&typeof r.source==='string');
      cache.completed=Date.now();
    }).catch(()=>{cache.rows=[];cache.error=true;}).finally(()=>{cache.pending=null;window.dispatchEvent(new CustomEvent(REPORT_EVENT));});
  }
  function weatherStatus(h,c,t){
    const helper=h.states[c.entity];
    if(!helper||helper.state==='unavailable')return t.missing_helper;
    const id=(helper.state||'').trim();
    if(!id||['unknown','Not set','not set'].includes(id))return t.none;
    const source=h.states[id];if(!source)return t.missing_source;
    if(!c.domains.includes(id.split('.')[0]))return t.wrong_domain+': '+c.domains.join(', ');
    if(source.state==='unavailable')return t.unavailable;
    if(source.state==='unknown')return t.unknown_value;
    if(c.units&&!c.units.includes(source.attributes?.unit_of_measurement))return t.wrong_unit+': '+c.units.join(', ');
    const value=String(source.state??'').trim();
    if(!value||(c.units&&(!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(value)||!Number.isFinite(Number(value))||(c.units.includes('mm')&&Number(value)<0)))||(c.domains.includes('binary_sensor')&&!['on','off'].includes(value)))return t.invalid_value;
    return t.healthy;
  }
  function timestamp(value,h){const date=new Date(value);if(!value||!Number.isFinite(date.getTime()))return '';try{return new Intl.DateTimeFormat(h.locale?.language||h.language||undefined,{dateStyle:'short',timeStyle:'medium',timeZone:h.config?.time_zone}).format(date);}catch{return date.toISOString();}}
  class EntityPicker extends HTMLElement {
    constructor(){
      super();this.attachShadow({mode:'open'});this._serial=++EntityPicker.serial;this._appearance=()=>paint(this,this._hass);
      this.shadowRoot.innerHTML=`<style>${commonCSS}.open{width:100%;text-align:left;border:0;border-bottom:1px solid var(--divider-color);border-radius:0;display:grid;gap:3px;padding:8px 0;background:transparent}.value{color:var(--secondary-text-color);font-size:12px;overflow-wrap:anywhere}.edit{padding:8px 0}.search{box-sizing:border-box;min-height:44px;width:100%;padding:10px;border-radius:8px;border:1px solid var(--divider-color);background:var(--input-fill-color,var(--card-background-color))}.list{max-height:240px;overflow:auto;margin:6px 0;border:1px solid var(--divider-color);border-radius:8px}.option{width:100%;display:block;border:0;border-radius:0;border-bottom:1px solid var(--divider-color);text-align:left;padding:8px;min-height:52px}.option[aria-selected="true"]{box-shadow:inset 4px 0 var(--accent-color)}.option small{display:block;color:var(--secondary-text-color);overflow-wrap:anywhere}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.save{border:2px solid var(--accent-color)}.note,.error{font-size:13px;margin:6px 0;overflow-wrap:anywhere}.error{color:var(--error-color,#c43c32)}.selected{overflow-wrap:anywhere}</style><button class="open" type="button" aria-expanded="false"><span class="name"></span><span class="value"></span></button><div class="edit" hidden><input class="search" type="search" autocomplete="off" role="combobox" aria-autocomplete="list" aria-expanded="true"><div class="list" role="listbox"></div><div class="note" role="status"></div><div class="selected"></div><div class="actions"><button class="save" type="button"></button><button class="cancel" type="button"></button><button class="clear" type="button"></button></div><div class="error" role="alert"></div></div>`;
      const info=document.createElement('div');info.className='diagnostics';info.hidden=true;info.innerHTML=`<style>.diagnostics{font-size:12px;line-height:1.5;padding:5px 0 12px;color:var(--secondary-text-color);overflow-wrap:anywhere}.health{font-weight:600}.health[data-ok="false"]{color:var(--error-color)}.kind{font-weight:600}.refresh{font-size:12px;margin-top:4px}.hint{margin:4px 0;max-width:60ch}</style><div class="kind"></div><div class="health" role="status"></div><div class="reading"></div><div class="reported"></div><div class="updated"></div><div class="checked"></div><details><summary></summary><div class="hint"></div><div class="polarity"></div></details><button type="button" class="refresh"></button>`;this.shadowRoot.querySelector('.open').after(info);
      this._reports=()=>this._diagnostics();
      const $=s=>this.shadowRoot.querySelector(s);this.$=$;$('.refresh').addEventListener('click',()=>{loadReports(this._hass,true);this._diagnostics();});$('.open').addEventListener('click',()=>this._open());$('.search').addEventListener('input',()=>{this._query=$('.search').value;this._active=-1;this._list();});$('.search').addEventListener('keydown',e=>this._key(e));$('.cancel').addEventListener('click',()=>this._close());$('.clear').addEventListener('click',()=>{this._draft='';this._error('');this._selected();});$('.save').addEventListener('click',()=>this._save());
    }
    setConfig(c){if(!/^input_text\.irrigation_(zone\d+_switch_entity_id|external_sensor_[a-z0-9_]+|cycle[12]_wait_for_entity_name|notification_script|log_notify_entity|announcement_script|announcement_player|startup_ready_entity|ha_stopping_entity)$/.test(c.entity)||!Array.isArray(c.domains)||!c.domains.length)throw Error('A supported irrigation mapping and domains are required');this._config={...c,diagnostic_kind:c.diagnostic_kind||weatherKind(c.entity)};this._t=labels(c);this._editing=false;this._render();}
    set hass(h){const old=this._hass;this._hass=h;this._render();if(this._editing && old?.states!==h.states){this._list();this._selected();}}
    connectedCallback(){window.addEventListener(EVENT,this._appearance);window.addEventListener(REPORT_EVENT,this._reports);this._render();}
    disconnectedCallback(){window.removeEventListener(EVENT,this._appearance);window.removeEventListener(REPORT_EVENT,this._reports);}
    _render(){
      if(!this._config||!this._hass)return;paint(this,this._hass);const t=this._t;const s=this._hass.states[this._config.entity];const value=s?.state||'';this.$('.name').textContent=this._config.name||s?.attributes?.friendly_name||this._config.entity;this.$('.value').textContent=value==='unavailable'?t.unavailable:(['unknown',''].includes(value)?t.none:value);this.$('.open').disabled=!s||s.state==='unavailable';this.$('.save').textContent=t.save;this.$('.cancel').textContent=t.cancel;this.$('.clear').textContent=t.clear;this.$('.search').placeholder=t.search;this.$('.search').setAttribute('aria-label',t.search+' — '+this.$('.name').textContent);this.$('.list').id='ig-options-'+this._serial;this.$('.search').setAttribute('aria-controls',this.$('.list').id);
      if(this.isConnected&&this._config.diagnostic_kind)loadReports(this._hass);
      this._diagnostics();
    }
    _diagnostics(){
      if(!this._config||!this._hass)return;
      const t=this._t,h=this._hass,c=this._config;this.$('.diagnostics').hidden=!c.diagnostic_kind;if(!c.diagnostic_kind)return;
      const id=h.states[c.entity]?.state,source=h.states[id],cache=reportCache(h);
      // A delayed response must never attach the old source's report time to a
      // newly assigned entity, or to a state updated after that snapshot.
      const report=cache?.rows.find(r=>r.helper===c.entity&&r.source===id&&(!source?.last_updated||Date.parse(r.last_updated)===Date.parse(source.last_updated)));
      const health=weatherStatus(h,c,t);this.$('.kind').textContent=t[c.diagnostic_kind];this.$('.health').textContent=health;this.$('.health').dataset.ok=String(health===t.healthy);
      let reading=String(source?.state??'');
      if(c.units&&health===t.healthy)try{reading=new Intl.NumberFormat(h.locale?.language||h.language||undefined,{maximumSignificantDigits:6}).format(Number(reading));}catch{}
      this.$('.reading').textContent=t.value+': '+(source?reading+(source.attributes?.unit_of_measurement?' '+source.attributes.unit_of_measurement:''):'—');
      this.$('.reported').textContent=t.reported+': '+(timestamp(report?.last_reported,h)||(cache?.pending?t.loading:cache?.error?t.report_failed:t.no_report));
      this.$('.updated').textContent=t.updated+': '+(timestamp(source?.last_updated,h)||'—');
      this.$('.checked').textContent=cache?.completed&&!cache.error?t.checked+': '+timestamp(cache.completed,h):'';
      this.$('.refresh').textContent=t.refresh;this.$('.refresh').disabled=!!cache?.pending||!h.callApi;
      this.$('summary').textContent=t.reported+' ⓘ';this.$('.hint').textContent=t.report_hint;this.$('.polarity').textContent=c.entity.endsWith('_raining_now')?t.raining_on:'';
    }
    _open(){if(this._pending)return;this._baseline=this._hass.states[this._config.entity]?.state||'';this._draft=this._baseline;this._query='';this._active=-1;this._editing=true;this.$('.open').setAttribute('aria-expanded','true');this.$('.edit').hidden=false;this.$('.search').value='';this._error('');this._list();this._selected();this.$('.search').focus();}
    _close(){if(this._pending)return;this._editing=false;this.$('.edit').hidden=true;this.$('.open').setAttribute('aria-expanded','false');this.$('.open').focus();}
    _error(text){this.$('.error').textContent=text;}
    _selected(){this.$('.selected').textContent=this._draft||this._t.none;this.$('.save').disabled=!!this._pending||this._draft===this._baseline||(this._draft!==''&&!accepts(this._hass.states[this._draft],this._config));}
    _list(){
      const q=(this._query||'').trim().toLocaleLowerCase();const rows=Object.values(this._hass.states).filter(s=>accepts(s,this._config)&&(!q||(s.entity_id+' '+(s.attributes?.friendly_name||'')).toLocaleLowerCase().includes(q))).sort((a,b)=>(a.attributes?.friendly_name||a.entity_id).localeCompare(b.attributes?.friendly_name||b.entity_id));this._options=rows.slice(0,50);const list=this.$('.list');
      // State updates must not replace a focused option or interrupt typing.
      const signature=JSON.stringify(this._options.map(s=>[s.entity_id,s.attributes?.friendly_name,s.state==='unavailable']));
      if(signature!==this._signature){
        this._signature=signature;const focused=focusedWithin(this.shadowRoot);const activeId=this.shadowRoot.getElementById(this.$('.search').getAttribute('aria-activedescendant'))?.dataset.entity;const existing=new Map([...list.children].map(b=>[b.dataset.entity,b]));const keep=new Set();
        this._options.forEach((state,i)=>{
          let b=existing.get(state.entity_id);keep.add(state.entity_id);
          if(!b){b=document.createElement('button');b.type='button';b.className='option';b.setAttribute('role','option');b.dataset.entity=state.entity_id;b.append(document.createElement('span'),document.createElement('small'));b.addEventListener('click',()=>this._choose(state.entity_id));}
          b.id=`ig-option-${this._serial}-${i}`;const title=state.attributes?.friendly_name||state.entity_id;const detail=state.entity_id+(state.state==='unavailable'?' — '+this._t.unavailable:'');if(b.children[0].textContent!==title)b.children[0].textContent=title;if(b.children[1].textContent!==detail)b.children[1].textContent=detail;if(list.children[i]!==b)list.insertBefore(b,list.children[i]||null);
        });
        for(const b of [...list.children])if(!keep.has(b.dataset.entity))b.remove();
        if(focused?.dataset.entity&&keep.has(focused.dataset.entity)&&focusedWithin(this.shadowRoot)!==focused)focused.focus();
        if(activeId){this._active=this._options.findIndex(state=>state.entity_id===activeId);if(this._active>=0)this.$('.search').setAttribute('aria-activedescendant',list.children[this._active].id);else this.$('.search').removeAttribute('aria-activedescendant');}
      }
      for(const b of list.children)b.setAttribute('aria-selected',String(b.dataset.entity===this._draft));
      this.$('.note').textContent=rows.length===0?this._t.empty:(rows.length>50?rows.length+' '+this._t.more:'');
    }
    _choose(id){if(this._pending)return;this._draft=id;this._error('');this._list();this._selected();}
    _key(e){if(e.key==='Escape'){e.preventDefault();this._close();return;}if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();const n=this._options.length;if(!n)return;this._active=(this._active+(e.key==='ArrowDown'?1:-1)+n)%n;const b=this.$('.list').children[this._active];this.$('.search').setAttribute('aria-activedescendant',b.id);b.scrollIntoView({block:'nearest'});}else if(e.key==='Enter'&&this._active>=0){e.preventDefault();const s=this._options[this._active];if(s)this._choose(s.entity_id);}}
    async _save(){
      if(this._pending)return;const h=this._hass;const value=this._draft;const current=h.states[this._config.entity]?.state;
      if(current!==this._baseline){this._error(this._t.changed);return;}
      if(value!==''&&!accepts(h.states[value],this._config)){this._error(this._t.invalid);return;}
      if(this._config.guard_watering&&watering(h)){this._error(this._t.busy);return;}
      if(value===current)return;this._pending=true;for(const b of this.shadowRoot.querySelectorAll('button'))b.disabled=true;this.$('.search').disabled=true;
      try{await h.callService('input_text','set_value',{entity_id:this._config.entity,value});this._pending=false;this._close();}catch{this._error(this._t.failed);}finally{this._pending=false;for(const b of this.shadowRoot.querySelectorAll('button'))b.disabled=false;this.$('.search').disabled=false;this._selected();this._render();}
    }
  }
  // This card only renders engine snapshots; it never calls services or a network API.
  class DecisionJournal extends HTMLElement {
    constructor() {
      super(); this.attachShadow({mode:'open'});
      this.shadowRoot.innerHTML=`<style>${commonCSS}
        ha-card{display:block;padding:16px;border-radius:12px;background:var(--card-background-color);border:1px solid var(--divider-color)}
        h2{font-size:18px;margin:0 0 10px}p{margin:5px 0;overflow-wrap:anywhere}.context,.at,.hint{color:var(--secondary-text-color);font-size:13px}
        .reason{font-weight:600}.effects{font-size:14px}.hint{margin-top:12px}summary{cursor:pointer;min-height:44px;align-content:center}
        summary:focus-visible{outline:3px solid var(--accent-color);outline-offset:2px}ol{padding:0;list-style:none;margin:0;max-height:420px;overflow:auto}
        li{padding:12px 0;border-top:1px solid var(--divider-color)}.warning{color:var(--error-color)}
      </style><ha-card><h2></h2><div class="latest" aria-live="polite"></div><details><summary></summary><ol tabindex="0"></ol></details><p class="hint"></p></ha-card>`;
      this._appearance=()=>{if(this._hass)paint(this,this._hass);};
    }
    setConfig(c){this._config=c;this._signature=null;this._render();}
    set hass(h){this._hass=h;this._render();}
    connectedCallback(){window.addEventListener(EVENT,this._appearance);this._render();}
    disconnectedCallback(){window.removeEventListener(EVENT,this._appearance);}
    getCardSize(){return 3;}
    getGridOptions(){return {columns:12,rows:'auto'};}
    _render(){
      if(!this._hass||!this._config)return;
      paint(this,this._hass); const t={...decisionFallback,...this._config.ui_labels};
      const s=this._hass.states[this._config.entity||'sensor.irrigation_last_decision'];
      const records=Array.isArray(s?.attributes?.records)?s.attributes.records.filter(r=>r&&typeof r==='object'&&typeof r.reason==='string').slice(-64).reverse():[];
      const signature=JSON.stringify([records,!!s,t,this._hass.locale?.language,this._hass.config?.time_zone]);
      if(signature===this._signature)return;this._signature=signature;
      const q=x=>this.shadowRoot.querySelector(x);
      const text=(tag,value,cls)=>{const e=document.createElement(tag);e.textContent=String(value??'');if(cls)e.className=cls;return e;};
      const numeric=value=>value!==null&&value!==undefined&&String(value).trim()!==''&&Number.isFinite(Number(value));
      const time=value=>{if(!numeric(value))return '—';const n=Math.max(0,Math.round(Number(value)));return n>=60?`${Math.floor(n/60)} min${n%60?` ${n%60} s`:''}`:`${n} s`;};
      const row=r=>{
        const el=document.createElement('div');
        const cycle=/^cycle[123]$/.test(r.cycle)?`${t.cycle||'Cycle'} ${r.cycle.slice(-1)}`:'';
        const zone=Number.isInteger(Number(r.zone))&&Number(r.zone)>=1&&Number(r.zone)<=16?`${t.zone||'Zone'} ${r.zone}`:'';
        el.append(text('p',[r.cycle_name||cycle,r.zone_name||zone].filter(Boolean).join(' · '),'context'));
        let reason=t[r.reason]||t.unknown||r.reason;
        el.append(text('p',reason,'reason'));
        if(numeric(r.seconds))el.append(text('p',`${t.base}: ${numeric(r.base)?time(Number(r.base)*60):'—'} → ${t.selected}: ${time(r.seconds)}`,'duration'));
        const effects=[];
        const adjusted=r.rain===true||r.temperature===true;
        if(r.rain===true)effects.push(numeric(r.rain_factor)?`${t.rain}: ×${Number(r.rain_factor)} (${Math.round((Number(r.rain_factor)-1)*100)}%)`:t.factor_unknown);
        if(r.temperature===true)effects.push(numeric(r.temperature_factor)?`${t.temperature}: ×${Number(r.temperature_factor)} (${Math.round((Number(r.temperature_factor)-1)*100)}%)`:t.factor_unknown);
        const raw=Number(r.base)*60*(r.rain===true?Number(r.rain_factor):1)*(r.temperature===true?Number(r.temperature_factor):1);
        // Bounds are applied before testing-mode scaling and final rounding.
        if(adjusted&&raw!==0&&Number.isFinite(raw)){
          if(raw>Number(r.maximum))effects.push(`${t.maximum}: ${time(r.maximum)}`);
          else if(raw<Number(r.minimum))effects.push(`${t.minimum}: ${time(r.minimum)}`);
        }
        if(r.testing===true)effects.push(t.testing);
        if(r.physical===false)effects.push(t.simulation);
        for(const effect of effects.filter(Boolean))el.append(text('p',effect,'effects'));
        if(numeric(r.expected)&&numeric(r.seconds)&&Number(r.expected)!==Number(r.seconds))el.append(text('p',t.snapshot_mismatch,'warning'));
        if(r.rain_source)el.append(text('p',`${r.rain_source}: ${r.rain_state??'—'}`,'context'));
        if(r.source)el.append(text('p',`${r.source} → ${r.expected??'—'}${r.observed!==undefined?` (${r.observed})`:''}`,'context'));
        const date=new Date(r.at);
        let formatted=r.at||'';
        if(Number.isFinite(date.getTime())){try{formatted=new Intl.DateTimeFormat(this._hass.locale?.language||'en',{dateStyle:'short',timeStyle:'medium',timeZone:this._hass.config?.time_zone||'UTC'}).format(date);}catch{formatted=date.toISOString();}}
        el.append(text('p',formatted,'at'));return el;
      };
      q('h2').textContent=t.title||'Watering decisions';q('.hint').textContent=t.hint||'';
      q('summary').textContent=`${t.history||'Decision history'} (${records.length})`;
      q('ol').setAttribute('aria-label',t.history||'Decision history');q('details').hidden=records.length<2;
      q('.latest').replaceChildren(records.length?row(records[0]):text('p',s?t.empty:t.missing));
      q('ol').replaceChildren(...records.slice(1).map(r=>{const li=document.createElement('li');li.append(row(r));return li;}));
    }
  }

  EntityPicker.serial=0;
  for(const [name,element]of [['irrigation-garden-decisions',DecisionJournal],['irrigation-garden-themed-card',ThemedCard],['irrigation-garden-appearance',AppearanceButton],['irrigation-garden-entity-picker',EntityPicker]])if(!customElements.get(name))customElements.define(name,element);
  window.customCards=window.customCards||[];window.customCards.push({type:'irrigation-garden-appearance',name:'Irrigation Garden appearance',description:'Light/dark appearance for the original irrigation dashboard.'});
  console.info('Irrigation Garden UI '+VERSION);
})();
