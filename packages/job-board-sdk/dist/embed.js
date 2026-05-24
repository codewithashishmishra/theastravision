var AastraaJobBoard=(function(m){"use strict";const p=`
:host { display: block; font-family: system-ui, sans-serif; color: #111; }
.wrap { max-width: 720px; margin: 0 auto; }
.header { margin-bottom: 1rem; }
.header h2 { margin: 0; font-size: 1.25rem; }
.header p { margin: 0.25rem 0 0; color: #666; font-size: 0.875rem; }
.list { list-style: none; padding: 0; margin: 0; }
.card {
  border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem;
  margin-bottom: 0.5rem; cursor: pointer; background: #fff;
}
.card:hover { border-color: #d1d5db; }
.meta { font-size: 0.8rem; color: #6b7280; margin-top: 0.25rem; }
.back { background: none; border: none; color: var(--brand); cursor: pointer; font-size: 0.875rem; padding: 0; margin-bottom: 1rem; }
.jd { font-size: 0.9rem; line-height: 1.6; }
.jd p { margin: 0 0 0.75rem; }
.form label { display: block; font-size: 0.8rem; font-weight: 500; margin-bottom: 0.25rem; }
.form input, .form select { width: 100%; box-sizing: border-box; margin-bottom: 0.75rem; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 6px; }
.btn {
  background: var(--brand); color: #fff; border: none; border-radius: 6px;
  padding: 0.6rem 1.2rem; font-size: 0.875rem; cursor: pointer;
}
.btn:disabled { opacity: 0.6; cursor: wait; }
.msg { font-size: 0.875rem; margin-top: 0.5rem; }
.msg.err { color: #b91c1c; }
.msg.ok { color: #15803d; }
`;function f(){const i=document.currentScript;if(!i)return null;const e=i.getAttribute("data-api-base")||"http://127.0.0.1:8000/api/v1",t=i.getAttribute("data-api-key")||"",a=i.getAttribute("data-target")||"aastraa-job-board",n=i.getAttribute("data-theme")||"light",r=i.getAttribute("data-job-slug")||void 0,s=i.getAttribute("data-mode")||(r?"detail":"list");return t?{apiBase:e.replace(/\/$/,""),apiKey:t,target:a,theme:n,jobSlug:r,mode:s}:(console.error("[AastraaJobBoard] data-api-key is required"),null)}async function d(i,e,t){const a=`${i.apiBase}/public/job-board${e}`,n={"X-Job-Board-Key":i.apiKey,...t==null?void 0:t.headers},r=await fetch(a,{...t,headers:n}),s=await r.json();if(!r.ok)throw new Error(s.detail||"Request failed");return s}class h{constructor(e,t){this.config=null,this.selectedSlug=null,this.view="list",this.opts=t,this.host=e,this.shadow=e.attachShadow({mode:"open"});const a=document.createElement("style");a.textContent=p,this.shadow.appendChild(a),this.selectedSlug=t.jobSlug??null,this.view=t.mode==="detail"&&t.jobSlug?"detail":t.mode==="apply"&&t.jobSlug?"apply":"list",this.init()}async init(){try{this.config=await d(this.opts,"/config/"),this.shadow.host.style.setProperty("--brand",this.config.primary_color||"#2563eb"),await this.render()}catch(e){this.renderError(e instanceof Error?e.message:"Failed to load job board")}}wrap(){const e=document.createElement("div");return e.className="wrap",e}renderError(e){this.shadow.innerHTML="";const t=document.createElement("style");t.textContent=p,this.shadow.appendChild(t);const a=this.wrap();a.innerHTML=`<p class="msg err">${e}</p>`,this.shadow.appendChild(a)}async render(){this.shadow.querySelectorAll(".wrap").forEach(e=>e.remove()),this.view==="list"?await this.renderList():this.view==="detail"&&this.selectedSlug?await this.renderDetail(this.selectedSlug):this.view==="apply"&&this.selectedSlug&&await this.renderApply(this.selectedSlug)}header(){const e=this.config;return`<div class="header"><h2>${e.tenant_name}</h2>${e.company_blurb?`<p>${e.company_blurb}</p>`:""}</div>`}async renderList(){const e=await d(this.opts,"/jobs/"),t=this.wrap();t.innerHTML=this.header();const a=document.createElement("ul");a.className="list",e.results.forEach(n=>{const r=document.createElement("li");r.className="card",r.innerHTML=`<strong>${n.title}</strong><div class="meta">${[n.location,n.department,n.employment_type].filter(Boolean).join(" · ")}</div>`,r.addEventListener("click",()=>{this.selectedSlug=n.slug,this.view="detail",this.host.dispatchEvent(new CustomEvent("aastraa:job-selected",{detail:{slug:n.slug},bubbles:!0})),this.render()}),a.appendChild(r)}),e.results.length||(a.innerHTML='<li class="meta">No open positions.</li>'),t.appendChild(a),this.shadow.appendChild(t)}async renderDetail(e){const t=await d(this.opts,`/jobs/${e}/`),a=this.wrap(),n=document.createElement("button");n.className="back",n.textContent="← All jobs",n.addEventListener("click",()=>{this.view="list",this.selectedSlug=null,this.render()}),a.appendChild(n);const r=document.createElement("div");r.innerHTML=`${this.header()}<h3>${t.title}</h3><div class="meta">${[t.location,t.department].filter(Boolean).join(" · ")}</div><div class="jd">${t.description_html||""}</div>`,a.appendChild(r);const s=document.createElement("button");s.className="btn",s.textContent="Apply",s.style.marginTop="1rem",s.addEventListener("click",()=>{if(t.use_external_apply&&t.external_apply_url){window.open(t.external_apply_url,"_blank","noopener");return}this.view="apply",this.render()}),a.appendChild(s),this.shadow.appendChild(a)}async renderApply(e){const t=await d(this.opts,`/jobs/${e}/`),a=this.wrap(),n=document.createElement("button");n.className="back",n.textContent=`← ${t.title}`,n.addEventListener("click",()=>{this.view="detail",this.render()}),a.appendChild(n);const r=document.createElement("form");r.className="form",r.innerHTML=`
      <input type="text" name="website" style="display:none" tabindex="-1" autocomplete="off" />
      <label>First name *</label><input name="first_name" required />
      <label>Last name</label><input name="last_name" />
      <label>Email *</label><input name="email" type="email" required />
      <label>Phone</label><input name="phone" type="tel" />
      <label>Resume (PDF/DOCX) *</label><input name="resume_file" type="file" accept=".pdf,.docx" required />
      <button type="submit" class="btn">Submit application</button>
      <p class="msg" id="form-msg"></p>
    `,r.addEventListener("submit",async s=>{s.preventDefault();const o=r.querySelector("#form-msg"),b=r.querySelector(".btn");b.disabled=!0,o.textContent="",o.className="msg";try{const l=new FormData(r),g=await fetch(`${this.opts.apiBase}/public/job-board/jobs/${e}/apply/`,{method:"POST",headers:{"X-Job-Board-Key":this.opts.apiKey},body:l}),c=await g.json();if(!g.ok)throw new Error(c.detail||"Failed");if(c.redirect_url){window.location.href=c.redirect_url;return}o.textContent=c.message||"Application submitted.",o.className="msg ok",this.host.dispatchEvent(new CustomEvent("aastraa:applied",{detail:{slug:e},bubbles:!0}))}catch(l){o.textContent=l instanceof Error?l.message:"Error",o.className="msg err",b.disabled=!1}}),a.appendChild(r),this.shadow.appendChild(a)}}function u(){const i=f();if(!i)return;const e=document.getElementById(i.target);if(!e){console.error(`[AastraaJobBoard] #${i.target} not found`);return}new h(e,i)}return document.readyState==="loading"?document.addEventListener("DOMContentLoaded",u):u(),m.JobBoardWidget=h,Object.defineProperty(m,Symbol.toStringTag,{value:"Module"}),m})({});
