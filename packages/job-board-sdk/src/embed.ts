/**
 * AASTRAA Job Board embed SDK — mount on any website via script tag.
 *
 * <script src="https://cdn.aastraa.com/job-board/v1/embed.js"
 *   data-api-base="https://api.example.com/api/v1"
 *   data-api-key="jb_live_..."
 *   data-target="aastraa-job-board"
 *   data-theme="light"></script>
 * <div id="aastraa-job-board"></div>
 */

type JobItem = {
  slug: string;
  title: string;
  location: string;
  department: string | null;
  employment_type: string;
  work_mode: string;
};

type PortalConfig = {
  tenant_name: string;
  primary_color: string;
  company_blurb: string;
};

type EmbedOptions = {
  apiBase: string;
  apiKey: string;
  target: string;
  theme: string;
  jobSlug?: string;
  mode?: 'list' | 'detail' | 'apply';
};

const STYLES = `
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
`;

function getScriptOptions(): EmbedOptions | null {
  const script = document.currentScript as HTMLScriptElement | null;
  if (!script) return null;
  const apiBase = script.getAttribute('data-api-base') || 'http://127.0.0.1:8000/api/v1';
  const apiKey = script.getAttribute('data-api-key') || '';
  const target = script.getAttribute('data-target') || 'aastraa-job-board';
  const theme = script.getAttribute('data-theme') || 'light';
  const jobSlug = script.getAttribute('data-job-slug') || undefined;
  const mode = (script.getAttribute('data-mode') as EmbedOptions['mode']) || (jobSlug ? 'detail' : 'list');
  if (!apiKey) {
    console.error('[AastraaJobBoard] data-api-key is required');
    return null;
  }
  return { apiBase: apiBase.replace(/\/$/, ''), apiKey, target, theme, jobSlug, mode };
}

async function apiFetch<T>(opts: EmbedOptions, path: string, init?: RequestInit): Promise<T> {
  const url = `${opts.apiBase}/public/job-board${path}`;
  const headers: Record<string, string> = {
    'X-Job-Board-Key': opts.apiKey,
    ...(init?.headers as Record<string, string> | undefined),
  };
  const res = await fetch(url, { ...init, headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data as T;
}

class JobBoardWidget {
  private host: HTMLElement;
  private shadow: ShadowRoot;
  private opts: EmbedOptions;
  private config: PortalConfig | null = null;
  private selectedSlug: string | null = null;
  private view: 'list' | 'detail' | 'apply' = 'list';

  constructor(mountEl: HTMLElement, opts: EmbedOptions) {
    this.opts = opts;
    this.host = mountEl;
    this.shadow = mountEl.attachShadow({ mode: 'open' });
    const style = document.createElement('style');
    style.textContent = STYLES;
    this.shadow.appendChild(style);
    this.selectedSlug = opts.jobSlug ?? null;
    this.view = opts.mode === 'detail' && opts.jobSlug ? 'detail' : opts.mode === 'apply' && opts.jobSlug ? 'apply' : 'list';
    void this.init();
  }

  private async init() {
    try {
      this.config = await apiFetch<PortalConfig>(this.opts, '/config/');
      this.shadow.host.style.setProperty('--brand', this.config.primary_color || '#2563eb');
      await this.render();
    } catch (e) {
      this.renderError(e instanceof Error ? e.message : 'Failed to load job board');
    }
  }

  private wrap(): HTMLElement {
    const el = document.createElement('div');
    el.className = 'wrap';
    return el;
  }

  private renderError(msg: string) {
    this.shadow.innerHTML = '';
    const style = document.createElement('style');
    style.textContent = STYLES;
    this.shadow.appendChild(style);
    const w = this.wrap();
    w.innerHTML = `<p class="msg err">${msg}</p>`;
    this.shadow.appendChild(w);
  }

  private async render() {
    this.shadow.querySelectorAll('.wrap').forEach((n) => n.remove());
    if (this.view === 'list') await this.renderList();
    else if (this.view === 'detail' && this.selectedSlug) await this.renderDetail(this.selectedSlug);
    else if (this.view === 'apply' && this.selectedSlug) await this.renderApply(this.selectedSlug);
  }

  private header(): string {
    const c = this.config!;
    return `<div class="header"><h2>${c.tenant_name}</h2>${c.company_blurb ? `<p>${c.company_blurb}</p>` : ''}</div>`;
  }

  private async renderList() {
    const data = await apiFetch<{ results: JobItem[] }>(this.opts, '/jobs/');
    const w = this.wrap();
    w.innerHTML = this.header();
    const ul = document.createElement('ul');
    ul.className = 'list';
    data.results.forEach((job) => {
      const li = document.createElement('li');
      li.className = 'card';
      li.innerHTML = `<strong>${job.title}</strong><div class="meta">${[job.location, job.department, job.employment_type].filter(Boolean).join(' · ')}</div>`;
      li.addEventListener('click', () => {
        this.selectedSlug = job.slug;
        this.view = 'detail';
        this.host.dispatchEvent(new CustomEvent('aastraa:job-selected', { detail: { slug: job.slug }, bubbles: true }));
        void this.render();
      });
      ul.appendChild(li);
    });
    if (!data.results.length) {
      ul.innerHTML = '<li class="meta">No open positions.</li>';
    }
    w.appendChild(ul);
    this.shadow.appendChild(w);
  }

  private async renderDetail(slug: string) {
    const job = await apiFetch<JobItem & { description_html: string; use_external_apply: boolean; external_apply_url?: string }>(
      this.opts,
      `/jobs/${slug}/`,
    );
    const w = this.wrap();
    const back = document.createElement('button');
    back.className = 'back';
    back.textContent = '← All jobs';
    back.addEventListener('click', () => {
      this.view = 'list';
      this.selectedSlug = null;
      void this.render();
    });
    w.appendChild(back);
    const inner = document.createElement('div');
    inner.innerHTML = `${this.header()}<h3>${job.title}</h3><div class="meta">${[job.location, job.department].filter(Boolean).join(' · ')}</div><div class="jd">${job.description_html || ''}</div>`;
    w.appendChild(inner);
    const btn = document.createElement('button');
    btn.className = 'btn';
    btn.textContent = 'Apply';
    btn.style.marginTop = '1rem';
    btn.addEventListener('click', () => {
      if (job.use_external_apply && job.external_apply_url) {
        window.open(job.external_apply_url, '_blank', 'noopener');
        return;
      }
      this.view = 'apply';
      void this.render();
    });
    w.appendChild(btn);
    this.shadow.appendChild(w);
  }

  private async renderApply(slug: string) {
    const job = await apiFetch<{ title: string }>(this.opts, `/jobs/${slug}/`);
    const w = this.wrap();
    const back = document.createElement('button');
    back.className = 'back';
    back.textContent = `← ${job.title}`;
    back.addEventListener('click', () => {
      this.view = 'detail';
      void this.render();
    });
    w.appendChild(back);
    const form = document.createElement('form');
    form.className = 'form';
    form.innerHTML = `
      <input type="text" name="website" style="display:none" tabindex="-1" autocomplete="off" />
      <label>First name *</label><input name="first_name" required />
      <label>Last name</label><input name="last_name" />
      <label>Email *</label><input name="email" type="email" required />
      <label>Phone</label><input name="phone" type="tel" />
      <label>Resume (PDF/DOCX) *</label><input name="resume_file" type="file" accept=".pdf,.docx" required />
      <button type="submit" class="btn">Submit application</button>
      <p class="msg" id="form-msg"></p>
    `;
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = form.querySelector('#form-msg') as HTMLElement;
      const btn = form.querySelector('.btn') as HTMLButtonElement;
      btn.disabled = true;
      msg.textContent = '';
      msg.className = 'msg';
      try {
        const fd = new FormData(form);
        const res = await fetch(`${this.opts.apiBase}/public/job-board/jobs/${slug}/apply/`, {
          method: 'POST',
          headers: { 'X-Job-Board-Key': this.opts.apiKey },
          body: fd,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed');
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
          return;
        }
        msg.textContent = data.message || 'Application submitted.';
        msg.className = 'msg ok';
        this.host.dispatchEvent(new CustomEvent('aastraa:applied', { detail: { slug }, bubbles: true }));
      } catch (err) {
        msg.textContent = err instanceof Error ? err.message : 'Error';
        msg.className = 'msg err';
        btn.disabled = false;
      }
    });
    w.appendChild(form);
    this.shadow.appendChild(w);
  }
}

function mount() {
  const opts = getScriptOptions();
  if (!opts) return;
  const el = document.getElementById(opts.target);
  if (!el) {
    console.error(`[AastraaJobBoard] #${opts.target} not found`);
    return;
  }
  new JobBoardWidget(el, opts);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mount);
} else {
  mount();
}

export { JobBoardWidget };
