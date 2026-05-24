(function () {
  if (!window.AASTRAA_PRICING) {
    console.warn('AASTRAA pricing: pricing-config.js did not load — showing static prices only.');
    return;
  }

  const {
    PRICING,
    PLAN_IDS,
    PLAN_LABELS,
    ADDONS,
    COMPARISON_ROWS,
    REGION_COMPLIANCE,
    AI_CREDIT_OVERAGE,
    getPlanPriceDisplay,
    getAddonPriceDisplay,
    getPlanIntlReference,
    getAddonIntlReference,
    detectDefaultRegion,
  } = window.AASTRAA_PRICING;

  const regionSelect = document.getElementById('pricing-region');
  const billingMonthly = document.getElementById('billing-monthly');
  const billingAnnual = document.getElementById('billing-annual');
  const modelHint = document.getElementById('pricing-model-hint');
  const pricingIntro = document.getElementById('pricing-intro');
  const pricingLive = document.getElementById('pricing-live-region');
  const comparisonBody = document.getElementById('comparison-body');
  const comparisonMobile = document.getElementById('comparison-cards-mobile');
  const complianceStatutory = document.getElementById('compliance-statutory');
  const complianceEngine = document.getElementById('compliance-engine');
  const complianceAttendance = document.getElementById('compliance-attendance');
  const contactRegion = document.getElementById('contact-pricing-region');
  const contactBilling = document.getElementById('contact-pricing-billing');
  const contactSelectedPlan = document.getElementById('contact-selected-plan');
  const contactPlanBanner = document.getElementById('contact-plan-banner');
  const contactFormPanel = document.getElementById('contact-form-panel');
  const addonsContainer = document.getElementById('pricing-addons');
  const aiCreditsFootnote = document.getElementById('pricing-ai-footnote');
  const intlTbody = document.getElementById('pricing-intl-tbody');
  const intlFootnote = document.getElementById('pricing-intl-footnote');

  let state = {
    region: detectDefaultRegion(),
    billing: 'monthly',
  };

  function loadPrefs() {
    try {
      const raw = localStorage.getItem('aastraa_pricing_prefs');
      if (!raw) return;
      const p = JSON.parse(raw);
      if (p.region && PRICING[p.region]) state.region = p.region;
      if (p.billing === 'annual' || p.billing === 'monthly') state.billing = p.billing;
    } catch (_) { /* ignore */ }
  }

  function savePrefs() {
    try {
      localStorage.setItem(
        'aastraa_pricing_prefs',
        JSON.stringify({ region: state.region, billing: state.billing })
      );
    } catch (_) { /* ignore */ }
  }

  function syncControls() {
    if (regionSelect) regionSelect.value = state.region;
    if (billingMonthly && billingAnnual) {
      const isAnnual = state.billing === 'annual';
      billingMonthly.setAttribute('aria-pressed', String(!isAnnual));
      billingAnnual.setAttribute('aria-pressed', String(isAnnual));
      billingMonthly.classList.toggle('bg-white', !isAnnual);
      billingMonthly.classList.toggle('shadow-sm', !isAnnual);
      billingMonthly.classList.toggle('text-slate-900', !isAnnual);
      billingMonthly.classList.toggle('text-slate-600', isAnnual);
      billingAnnual.classList.toggle('bg-white', isAnnual);
      billingAnnual.classList.toggle('shadow-sm', isAnnual);
      billingAnnual.classList.toggle('text-slate-900', isAnnual);
      billingAnnual.classList.toggle('text-slate-600', !isAnnual);
    }
  }

  function cellIcon(value) {
    if (value === true) {
      return '<i class="fa-solid fa-check text-green-500" aria-hidden="true"></i><span class="sr-only">Included</span>';
    }
    if (value === false) {
      return '<i class="fa-solid fa-minus text-slate-300" aria-hidden="true"></i><span class="sr-only">Not included</span>';
    }
    return `<span class="text-slate-700 font-medium text-sm">${value}</span>`;
  }

  function cellValueLabel(value) {
    if (value === true) return 'Included';
    if (value === false) return 'Not included';
    return String(value);
  }

  function cellValueClass(value) {
    if (value === true) return 'text-green-600';
    if (value === false) return 'text-slate-400';
    return 'text-slate-800 font-semibold';
  }

  function buildPlanInquiryMessage(planId) {
    const region = PRICING[state.region];
    const planLabel = PLAN_LABELS[planId] || planId;
    const display = getPlanPriceDisplay(state.region, planId, state.billing);
    const billingLabel = state.billing === 'annual' ? 'Annual billing (10% off)' : 'Monthly billing';
    let priceLine = `${display.main}${display.period}`;
    if (display.note) priceLine += ` (${display.note})`;
    if (display.strikethrough) priceLine += ` — was ${display.strikethrough}`;

    return `I am interested in the AASTRAA HRMS ${planLabel} plan.

Region: ${region.label}
Billing: ${billingLabel}
Quoted price: ${priceLine}

Please schedule a demo and share onboarding steps for our organization. We would like to discuss rollout timeline and user count.`;
  }

  function refreshFormLabels() {
    document.querySelectorAll('#contactForm .form-input').forEach((input) => {
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });
  }

  function goToContactWithPlan(planId) {
    if (!PLAN_IDS.includes(planId)) return;

    const region = PRICING[state.region];
    const planLabel = PLAN_LABELS[planId];
    const message = document.getElementById('message');

    if (contactRegion) contactRegion.value = state.region;
    if (contactBilling) contactBilling.value = state.billing;
    if (contactSelectedPlan) contactSelectedPlan.value = planId;

    if (message) {
      message.value = buildPlanInquiryMessage(planId);
      refreshFormLabels();
    }

    if (contactPlanBanner) {
      contactPlanBanner.textContent = `Selected: ${planLabel} · ${region.label} · ${state.billing === 'annual' ? 'Annual' : 'Monthly'}`;
      contactPlanBanner.classList.remove('hidden');
    }

    const contactSection = document.getElementById('contact');
    if (contactSection) {
      contactSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    if (contactFormPanel) {
      contactFormPanel.classList.add('contact-form-highlight');
      setTimeout(() => contactFormPanel.classList.remove('contact-form-highlight'), 3200);
    }

    setTimeout(() => {
      const nameInput = document.getElementById('name');
      if (nameInput) nameInput.focus();
    }, 450);

    window.AASTRAA_PRICING_STATE = { ...state, selectedPlan: planId };
  }

  function renderAddons() {
    if (!addonsContainer || !ADDONS?.length) return;
    addonsContainer.innerHTML = ADDONS.map((addon) => {
      const display = getAddonPriceDisplay(state.region, addon.id);
      if (!display) return '';
      const intl = getAddonIntlReference(state.region, addon.id);
      return `
      <article class="bg-white rounded-2xl border border-slate-200 p-6 shadow-material flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="flex-1">
          <h4 class="text-lg font-bold text-slate-900">${addon.name}</h4>
          <p class="text-sm text-slate-600 mt-1">${addon.description}</p>
          <p class="text-xs text-slate-500 mt-2">${display.note}${intl ? ` · ${intl}` : ''}</p>
        </div>
        <div class="text-right shrink-0">
          <span class="text-3xl font-black text-slate-900">${display.main}</span>
          <span class="text-slate-500 font-medium">${display.period}</span>
        </div>
      </article>`;
    }).join('');
  }

  function renderIntlMatrix() {
    if (!intlTbody) return;
    const billing = state.billing;
    intlTbody.innerHTML = PLAN_IDS.map((planId) => {
      const label = PLAN_LABELS[planId];
      const inD = getPlanPriceDisplay('IN', planId, billing);
      const usD = getPlanPriceDisplay('US', planId, billing);
      const caD = getPlanPriceDisplay('CA', planId, billing);
      const inCell = `${inD.main}${inD.period}`;
      const usCell = `${usD.main}${usD.period}`;
      const caCell = `${caD.main}${caD.period}`;
      return `<tr class="border-b border-slate-100 last:border-0"><th scope="row" class="text-left py-2 pr-2 font-medium text-slate-900">${label}</th><td class="py-2 px-2 text-center">${inCell}</td><td class="py-2 px-2 text-center">${usCell}</td><td class="py-2 pl-2 text-center">${caCell}</td></tr>`;
    }).join('');

    if (intlFootnote) {
      const job = getAddonPriceDisplay('IN', 'job_portal');
      const jobUs = getAddonPriceDisplay('US', 'job_portal');
      const jobCa = getAddonPriceDisplay('CA', 'job_portal');
      const annualNote =
        billing === 'annual' ? ' Prices shown with 10% annual discount.' : '';
      intlFootnote.textContent = `India: flat fee includes first 100 users. US & Canada: per active user.${annualNote} Job Portal add-on: ${job.main} · ${jobUs.main} · ${jobCa.main}/mo.`;
    }
  }

  function renderPlanCards() {
    const region = PRICING[state.region];
    document.querySelectorAll('[data-plan]').forEach((card) => {
      const planId = card.getAttribute('data-plan');
      const display = getPlanPriceDisplay(state.region, planId, state.billing);
      const amountEl = card.querySelector('[data-price-amount]');
      const periodEl = card.querySelector('[data-price-period]');
      const noteEl = card.querySelector('[data-price-note]');
      const strikeEl = card.querySelector('[data-price-strike]');
      const overageEl = card.querySelector('[data-price-overage]');

      if (amountEl) amountEl.textContent = display.main;
      if (periodEl) periodEl.textContent = display.period;
      if (noteEl) {
        noteEl.textContent = display.note;
        noteEl.classList.toggle('hidden', !display.note);
      }
      if (strikeEl) {
        strikeEl.textContent = display.strikethrough;
        strikeEl.classList.toggle('hidden', !display.strikethrough);
      }
      if (overageEl) {
        overageEl.innerHTML = display.overageHtml;
        overageEl.classList.toggle('hidden', !display.overageHtml);
      }
      const intlEl = card.querySelector('[data-price-intl]');
      if (intlEl) {
        const intl = getPlanIntlReference(state.region, planId, state.billing);
        intlEl.textContent = intl;
        intlEl.classList.toggle('hidden', !intl);
      }
    });

    renderIntlMatrix();

    if (modelHint) modelHint.textContent = region.modelHint;
    if (pricingIntro) {
      pricingIntro.textContent =
        region.model === 'flat'
          ? 'Choose the right tier to automate your entire HR lifecycle. India plans include your first 100 users.'
          : 'Choose the right tier to automate your entire HR lifecycle. Billed per active user.';
    }
    if (pricingLive) {
      pricingLive.textContent = `${region.label} · ${state.billing === 'annual' ? 'Annual (10% off)' : 'Monthly'} pricing`;
    }
    if (aiCreditsFootnote) {
      const overage = AI_CREDIT_OVERAGE[state.region] || AI_CREDIT_OVERAGE.GL;
      aiCreditsFootnote.innerHTML =
        '<strong>AI credits</strong> power the HR chatbot, resume parsing, and voice/video interviews. ' +
        'Credits reset each billing month. Typical use: chat message ≈ 1 credit · resume parse ≈ 5 credits · ' +
        'full AI interview ≈ 50 credits. Extra usage: <strong>' +
        overage +
        '</strong>, or add the <strong>AI Credit Pack</strong> below.';
    }
    document.documentElement.lang = region.lang;
    if (contactRegion) contactRegion.value = state.region;
    if (contactBilling) contactBilling.value = state.billing;
  }

  function renderComparisonTable() {
    if (!comparisonBody) return;
    comparisonBody.innerHTML = COMPARISON_ROWS.map(
      (row) => `
      <tr class="border-b border-slate-100 hover:bg-slate-50/50">
        <th scope="row" class="py-4 px-4 text-left text-sm font-medium text-slate-700">${row.label}</th>
        <td class="py-4 px-4 text-center">${cellIcon(row.values[0])}</td>
        <td class="py-4 px-4 text-center">${cellIcon(row.values[1])}</td>
        <td class="py-4 px-4 text-center">${cellIcon(row.values[2])}</td>
      </tr>`
    ).join('');
  }

  function renderComparisonMobileCards() {
    if (!comparisonMobile) return;

    const c = REGION_COMPLIANCE[state.region];
    const planMeta = [
      { id: 'starter', highlight: false, cta: 'Choose Starter' },
      { id: 'professional', highlight: true, cta: 'Choose Professional' },
      { id: 'enterprise', highlight: false, cta: 'Choose Enterprise' },
    ];

    comparisonMobile.innerHTML =
      planMeta
        .map((meta, planIndex) => {
          const planId = meta.id;
          const display = getPlanPriceDisplay(state.region, planId, state.billing);
          const label = PLAN_LABELS[planId];
          const base = meta.highlight
            ? 'bg-gradient-to-b from-slate-900 to-slate-800 text-white border-slate-700'
            : 'bg-white text-slate-900 border-slate-200';
          const featureRows = COMPARISON_ROWS.map((row) => {
            const val = row.values[planIndex];
            const valueClass = meta.highlight
              ? val === true
                ? 'text-green-400 font-medium'
                : val === false
                  ? 'text-slate-500'
                  : 'text-orange-200 font-semibold'
              : cellValueClass(val);
            const rowBorder = meta.highlight ? 'border-white/10' : 'border-slate-100';
            return `
            <li class="flex justify-between gap-3 py-2.5 border-b ${rowBorder} last:border-0 text-sm">
              <span class="${meta.highlight ? 'text-slate-300' : 'text-slate-600'}">${row.label}</span>
              <span class="${valueClass} shrink-0 text-right max-w-[48%]">${cellValueLabel(val)}</span>
            </li>`;
          }).join('');

          const btnClass = meta.highlight
            ? 'bg-primary-600 hover:bg-primary-700 text-white border-primary-500'
            : 'bg-slate-100 hover:bg-slate-200 text-slate-900 border-slate-200';

          return `
          <article class="rounded-2xl border shadow-material p-5 ${base} ${meta.highlight ? 'ring-2 ring-primary-500/50' : ''}">
            ${meta.highlight ? '<span class="inline-block text-[10px] font-bold uppercase tracking-wider bg-primary-600 text-white px-2 py-0.5 rounded mb-2">Most Popular</span>' : ''}
            <h3 class="text-xl font-bold">${label}</h3>
            <p class="mt-2 text-2xl font-black">${display.main}<span class="text-base font-medium opacity-80">${display.period}</span></p>
            ${display.note ? `<p class="text-xs mt-1 opacity-80">${display.note}</p>` : ''}
            <ul class="mt-4 space-y-0">${featureRows}</ul>
            <button type="button" class="plan-cta mt-5 w-full font-bold py-3 rounded-xl border transition-colors ${btnClass}" data-plan="${planId}">${meta.cta}</button>
          </article>`;
        })
        .join('') +
      `
      <article class="rounded-2xl border border-primary-100 bg-primary-50/50 p-5 text-sm text-slate-700">
        <h3 class="font-bold text-primary-800 uppercase text-xs tracking-wide mb-3">Regional compliance</h3>
        <dl class="space-y-2">
          <div><dt class="font-medium text-slate-800">Statutory payroll</dt><dd id="compliance-statutory-mobile">${c.statutory}</dd></div>
          <div><dt class="font-medium text-slate-800">Compliance engine</dt><dd id="compliance-engine-mobile">${c.engine}</dd></div>
          <div><dt class="font-medium text-slate-800">Attendance</dt><dd id="compliance-attendance-mobile">${c.attendance}</dd></div>
        </dl>
      </article>`;

    bindPlanCtaButtons(comparisonMobile);
  }

  function updateComplianceText() {
    const c = REGION_COMPLIANCE[state.region];
    if (complianceStatutory) complianceStatutory.textContent = c.statutory;
    if (complianceEngine) complianceEngine.textContent = c.engine;
    if (complianceAttendance) complianceAttendance.textContent = c.attendance;

    const proCompliance =
      state.region === 'IN'
        ? 'Full Statutory Compliance (PF, TDS, ESIC)'
        : state.region === 'US'
          ? 'US payroll tax compliance workflows'
          : 'International payroll compliance workflows';
    document.querySelectorAll('[data-compliance-statutory]').forEach((el) => {
      el.textContent = proCompliance;
    });
  }

  function renderComparison() {
    renderComparisonTable();
    renderComparisonMobileCards();
    renderAddons();
    updateComplianceText();
  }

  function bindPlanCtaButtons(root) {
    (root || document).querySelectorAll('.plan-cta').forEach((btn) => {
      if (btn.dataset.bound === '1') return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const planId = btn.getAttribute('data-plan');
        if (planId) goToContactWithPlan(planId);
      });
    });
  }

  function setBilling(billing) {
    state.billing = billing;
    savePrefs();
    syncControls();
    renderPlanCards();
    renderComparison();
  }

  function setRegion(region) {
    if (!PRICING[region]) return;
    state.region = region;
    savePrefs();
    syncControls();
    renderPlanCards();
    renderComparison();
  }

  function initPricing() {
    loadPrefs();
    syncControls();
    renderPlanCards();
    renderComparison();
    bindPlanCtaButtons(document);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPricing);
  } else {
    initPricing();
  }

  if (regionSelect) {
    regionSelect.addEventListener('change', (e) => setRegion(e.target.value));
  }
  if (billingMonthly) {
    billingMonthly.addEventListener('click', () => setBilling('monthly'));
  }
  if (billingAnnual) {
    billingAnnual.addEventListener('click', () => setBilling('annual'));
  }

  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener(
      'submit',
      () => {
        const msg = document.getElementById('message');
        if (!msg) return;
        const region = PRICING[state.region];
        const planId = contactSelectedPlan?.value;
        const planPart = planId ? `Plan: ${PLAN_LABELS[planId] || planId}. ` : '';
        const suffix = `\n\n[${planPart}Region: ${region.label}, ${state.billing === 'annual' ? 'Annual (10% off)' : 'Monthly'}]`;
        if (!msg.value.includes('[Region:')) {
          msg.value = msg.value.trim() + suffix;
        }
      },
      { capture: true }
    );
  }

  window.AASTRAA_selectPlan = goToContactWithPlan;
})();
