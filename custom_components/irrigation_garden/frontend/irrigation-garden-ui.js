/* Irrigation Garden UI: searchable mappings and local appearance, original engine unchanged. */
(() => {
  'use strict';
  const VERSION = '0.2.0b1';
  const EVENT = 'irrigation-garden-appearance';
  const memory = new Map();
  const palette = {
    light: {'primary-background-color':'#f4f6f8','secondary-background-color':'#ffffff','card-background-color':'#ffffff','ha-card-background':'#ffffff','primary-text-color':'#17212b','secondary-text-color':'#52606d','disabled-text-color':'#677684','divider-color':'#c5cdd4','ha-card-border-color':'#c5cdd4','accent-color':'#00796b','primary-color':'#00796b','state-icon-color':'#52606d','paper-item-icon-color':'#52606d','input-fill-color':'#edf1f4','input-ink-color':'#17212b','input-label-ink-color':'#52606d','mdc-theme-surface':'#ffffff','mdc-theme-on-surface':'#17212b','error-color':'#b3261e'},
    dark: {'primary-background-color':'#111827','secondary-background-color':'#1f2937','card-background-color':'#1f2937','ha-card-background':'#1f2937','primary-text-color':'#f3f4f6','secondary-text-color':'#cbd5e1','disabled-text-color':'#a5b1c2','divider-color':'#526176','ha-card-border-color':'#526176','accent-color':'#80cbc4','primary-color':'#80cbc4','state-icon-color':'#cbd5e1','paper-item-icon-color':'#cbd5e1','input-fill-color':'#273449','input-ink-color':'#f3f4f6','input-label-ink-color':'#cbd5e1','mdc-theme-surface':'#1f2937','mdc-theme-on-surface':'#f3f4f6','error-color':'#ffb4ab'}
  };
  const fallback = {search:'Search entities',save:'Save',cancel:'Cancel',clear:'Clear selection',none:'Not configured',empty:'No matching entities',unavailable:'Unavailable',invalid:'Select an existing compatible entity.',failed:'Save failed. Your previous setting is retained.',busy:'Stop watering and close mapped valves before changing valve assignments.',changed:'This setting changed elsewhere. Reopen the picker before saving.',more:'matching entities — type to narrow the list',dark:'Dark mode',light:'Light mode',to_dark:'Switch to dark mode',to_light:'Switch to light mode',loading:'Loading…',load_failed:'Cannot load the original card. Refresh the dashboard.'};
  const labels = c => ({...fallback,...c?.ui_labels});
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
  class EntityPicker extends HTMLElement {
    constructor(){
      super();this.attachShadow({mode:'open'});this._serial=++EntityPicker.serial;this._appearance=()=>paint(this,this._hass);
      this.shadowRoot.innerHTML=`<style>${commonCSS}.open{width:100%;text-align:left;border:0;border-bottom:1px solid var(--divider-color);border-radius:0;display:grid;gap:3px;padding:8px 0;background:transparent}.value{color:var(--secondary-text-color);font-size:12px;overflow-wrap:anywhere}.edit{padding:8px 0}.search{box-sizing:border-box;min-height:44px;width:100%;padding:10px;border-radius:8px;border:1px solid var(--divider-color);background:var(--input-fill-color,var(--card-background-color))}.list{max-height:240px;overflow:auto;margin:6px 0;border:1px solid var(--divider-color);border-radius:8px}.option{width:100%;display:block;border:0;border-radius:0;border-bottom:1px solid var(--divider-color);text-align:left;padding:8px;min-height:52px}.option[aria-selected="true"]{box-shadow:inset 4px 0 var(--accent-color)}.option small{display:block;color:var(--secondary-text-color);overflow-wrap:anywhere}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.save{border:2px solid var(--accent-color)}.note,.error{font-size:13px;margin:6px 0;overflow-wrap:anywhere}.error{color:var(--error-color,#c43c32)}.selected{overflow-wrap:anywhere}</style><button class="open" type="button" aria-expanded="false"><span class="name"></span><span class="value"></span></button><div class="edit" hidden><input class="search" type="search" autocomplete="off" role="combobox" aria-autocomplete="list" aria-expanded="true"><div class="list" role="listbox"></div><div class="note" role="status"></div><div class="selected"></div><div class="actions"><button class="save" type="button"></button><button class="cancel" type="button"></button><button class="clear" type="button"></button></div><div class="error" role="alert"></div></div>`;
      const $=s=>this.shadowRoot.querySelector(s);this.$=$;$('.open').addEventListener('click',()=>this._open());$('.search').addEventListener('input',()=>{this._query=$('.search').value;this._active=-1;this._list();});$('.search').addEventListener('keydown',e=>this._key(e));$('.cancel').addEventListener('click',()=>this._close());$('.clear').addEventListener('click',()=>{this._draft='';this._error('');this._selected();});$('.save').addEventListener('click',()=>this._save());
    }
    setConfig(c){if(!/^input_text\.irrigation_(zone\d+_switch_entity_id|external_sensor_[a-z0-9_]+|cycle[12]_wait_for_entity_name|notification_script|log_notify_entity|announcement_script|announcement_player|startup_ready_entity|ha_stopping_entity)$/.test(c.entity)||!Array.isArray(c.domains)||!c.domains.length)throw Error('A supported irrigation mapping and domains are required');this._config=c;this._t=labels(c);this._editing=false;this._render();}
    set hass(h){const old=this._hass;this._hass=h;this._render();if(this._editing && old?.states!==h.states){this._list();this._selected();}}
    connectedCallback(){window.addEventListener(EVENT,this._appearance);this._render();}
    disconnectedCallback(){window.removeEventListener(EVENT,this._appearance);}
    _render(){
      if(!this._config||!this._hass)return;paint(this,this._hass);const t=this._t;const s=this._hass.states[this._config.entity];const value=s?.state||'';this.$('.name').textContent=this._config.name||s?.attributes?.friendly_name||this._config.entity;this.$('.value').textContent=value==='unavailable'?t.unavailable:(['unknown',''].includes(value)?t.none:value);this.$('.open').disabled=!s||s.state==='unavailable';this.$('.save').textContent=t.save;this.$('.cancel').textContent=t.cancel;this.$('.clear').textContent=t.clear;this.$('.search').placeholder=t.search;this.$('.search').setAttribute('aria-label',t.search+' — '+this.$('.name').textContent);this.$('.list').id='ig-options-'+this._serial;this.$('.search').setAttribute('aria-controls',this.$('.list').id);
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
  EntityPicker.serial=0;
  for(const [name,element]of [['irrigation-garden-themed-card',ThemedCard],['irrigation-garden-appearance',AppearanceButton],['irrigation-garden-entity-picker',EntityPicker]])if(!customElements.get(name))customElements.define(name,element);
  window.customCards=window.customCards||[];window.customCards.push({type:'irrigation-garden-appearance',name:'Irrigation Garden appearance',description:'Light/dark appearance for the original irrigation dashboard.'});
  console.info('Irrigation Garden UI '+VERSION);
})();
