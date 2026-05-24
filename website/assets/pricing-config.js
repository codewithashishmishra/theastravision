/** AASTRAA HRMS regional pricing — aligned with docs/PRODUCTION_MONTHLY_COSTING.md */
const ANNUAL_DISCOUNT = 0.1;

const PLAN_IDS = ['starter', 'professional', 'enterprise'];

const PLAN_LABELS = {
  starter: 'Starter',
  professional: 'Professional',
  enterprise: 'Enterprise',
};

/** Shown in comparison table & plan footnotes (region-specific overage in modelHint where needed) */
const AI_CREDIT_OVERAGE = {
  IN: '₹2 per credit',
  US: '$0.025 per credit',
  CA: 'C$0.03 per credit',
  GL: '$0.025 per credit',
};

const PRICING = {
  IN: {
    id: 'IN',
    label: 'India (INR)',
    lang: 'en-IN',
    currency: 'INR',
    symbol: '₹',
    model: 'flat',
    modelHint:
      'Flat monthly fee includes your first 100 users. Additional users billed per month. AI usage is metered in monthly credits; top-up packs and per-credit overage available.',
    plans: {
      starter: { monthly: 8999, overage: 120, name: 'Starter', aiCredits: 200 },
      professional: { monthly: 12999, overage: 75, name: 'Professional', aiCredits: 1000 },
      enterprise: { monthly: 24999, overage: 60, name: 'Enterprise', aiCredits: 3000 },
    },
  },
  US: {
    id: 'US',
    label: 'United States (USD)',
    lang: 'en-US',
    currency: 'USD',
    symbol: '$',
    model: 'perUser',
    modelHint:
      'Per active user per month. AI features use a shared monthly credit pool per organization; credit packs available for heavy hiring.',
    plans: {
      starter: { monthly: 6, name: 'Starter', aiCredits: 200 },
      professional: { monthly: 14, name: 'Professional', aiCredits: 1000 },
      enterprise: { monthly: 22, name: 'Enterprise', aiCredits: 3000 },
    },
  },
  CA: {
    id: 'CA',
    label: 'Canada (CAD)',
    lang: 'en-CA',
    currency: 'CAD',
    symbol: 'C$',
    model: 'perUser',
    modelHint:
      'Per active user per month. CPP, EI & T4 compliance. AI credits included per plan with optional top-up packs.',
    plans: {
      starter: { monthly: 7, name: 'Starter', aiCredits: 200 },
      professional: { monthly: 15, name: 'Professional', aiCredits: 1000 },
      enterprise: { monthly: 23, name: 'Enterprise', aiCredits: 3000 },
    },
  },
  GL: {
    id: 'GL',
    label: 'Global (USD)',
    lang: 'en',
    currency: 'USD',
    symbol: '$',
    model: 'perUser',
    modelHint:
      'International billing in USD. Per active user per month. AI credits reset monthly; purchase add-on packs when you need more.',
    plans: {
      starter: { monthly: 6, name: 'Starter', aiCredits: 200 },
      professional: { monthly: 14, name: 'Professional', aiCredits: 1000 },
      enterprise: { monthly: 22, name: 'Enterprise', aiCredits: 3000 },
    },
  },
};

/** Optional add-ons (billed separately from core plans) */
const ADDONS = [
  {
    id: 'job_portal',
    name: 'Job Portal & Career Board SDK',
    description:
      'Greenhouse-style hosted careers page plus an embeddable job board for your website. Applications flow into your ATS pipeline.',
    pricing: {
      IN: { monthly: 2499, currency: 'INR' },
      US: { monthly: 7, currency: 'USD' },
      CA: { monthly: 7, currency: 'CAD' },
      GL: { monthly: 7, currency: 'USD' },
    },
  },
  {
    id: 'ai_credits',
    name: 'AI Credit Pack',
    description:
      '500 additional AI credits per month for voice/video interviews, resume parsing, and the HR chatbot. Stacks with your plan allowance.',
    pricing: {
      IN: { monthly: 1999, currency: 'INR' },
      US: { monthly: 25, currency: 'USD' },
      CA: { monthly: 25, currency: 'CAD' },
      GL: { monthly: 25, currency: 'USD' },
    },
  },
];

function getAddonPriceDisplay(regionId, addonId) {
  const addon = ADDONS.find((a) => a.id === addonId);
  if (!addon) return null;
  const region = PRICING[regionId];
  const price = addon.pricing[regionId] || addon.pricing.GL;
  const sym = region.symbol;
  return {
    main: formatMoney(price.monthly, sym, price.currency),
    period: '/mo',
    note: 'Add-on · billed in addition to your HRMS plan',
  };
}

/** Shared feature rows: starter | professional | enterprise */
const COMPARISON_ROWS = [
  { label: 'Core HR & employee database', values: [true, true, true] },
  { label: 'Employee Self-Service (ESS) portal', values: [true, true, true] },
  { label: 'QR, GPS & geo-fenced attendance', values: [true, true, true] },
  { label: 'Leave, shifts & overtime', values: [true, true, true] },
  { label: 'Recruitment ATS & candidate pipeline', values: [true, true, true] },
  { label: 'AI resume parsing & match scores', values: [false, true, true] },
  { label: 'Monthly AI credits included', values: ['200', '1,000', '3,000'] },
  { label: 'AI voice & video interviews (uses credits)', values: [false, true, true] },
  { label: 'WFH desktop tracker & sessions', values: [false, true, true] },
  { label: 'Policy-based screenshot capture (WFH)', values: [false, true, true] },
  { label: 'Payroll processing speed', values: ['24 hours', '10 hours', 'Instant'] },
  { label: 'AI HR helpdesk chatbot (uses credits)', values: [true, true, true] },
  { label: 'AI credit top-up packs', values: ['Available', 'Available', 'Available'] },
  { label: 'Support tier', values: ['24/7 AI', '24/7 Human + AI', 'VIP manager'] },
  { label: 'Expense, claims & reimbursements', values: [false, true, true] },
  { label: 'HR / IT helpdesk ticketing', values: [false, true, true] },
  { label: 'Face recognition liveness', values: [false, true, true] },
  { label: 'Onboarding & digital letters', values: [true, true, true] },
  { label: 'Engagement surveys & newsfeed', values: [false, true, true] },
  { label: 'Predictive attrition analytics', values: [false, false, true] },
  { label: 'Performance appraisals & OKRs', values: [false, false, true] },
  { label: 'Project timesheets (PSA) & billing', values: [false, false, true] },
  { label: 'Asset, exit & FnF settlement', values: [false, false, true] },
  { label: 'Multi-tenant & audit logs', values: [true, true, true] },
];

const REGION_COMPLIANCE = {
  IN: {
    statutory: 'PF, ESIC, Professional Tax, TDS & Form 16',
    engine: 'Indian statutory compliance engine',
    attendance: 'QR, GPS, face liveness & geo-fencing',
  },
  US: {
    statutory: 'US federal & state payroll tax workflows',
    engine: 'US tax withholding & international payroll support',
    attendance: 'QR, GPS, face liveness & geo-fencing',
  },
  CA: {
    statutory: 'CPP, EI, T4 & Quebec RL-1 workflows',
    engine: 'Canadian federal & provincial payroll engine',
    attendance: 'QR, GPS, face liveness & geo-fencing',
  },
  GL: {
    statutory: 'International payroll tax workflows',
    engine: 'Multi-country withholding & compliance support',
    attendance: 'QR, GPS, face liveness & geo-fencing',
  },
};

function formatMoney(amount, symbol, currency) {
  const n = Math.round(amount);
  if (currency === 'INR') {
    return symbol + n.toLocaleString('en-IN');
  }
  const hasCents = amount % 1 !== 0;
  return symbol + (hasCents ? amount.toFixed(2) : n.toLocaleString('en-US'));
}

function monthlyAfterAnnualDiscount(monthly) {
  return monthly * (1 - ANNUAL_DISCOUNT);
}

function annualTotal(monthly) {
  return monthly * 12 * (1 - ANNUAL_DISCOUNT);
}

function getPlanPriceDisplay(regionId, planId, billing) {
  const region = PRICING[regionId];
  const plan = region.plans[planId];
  const monthly = plan.monthly;
  const sym = region.symbol;

  if (billing === 'annual') {
    if (region.model === 'flat') {
      const annual = annualTotal(monthly);
      const equivMonthly = monthlyAfterAnnualDiscount(monthly);
      return {
        main: formatMoney(annual, sym, region.currency),
        period: '/yr',
        note: formatMoney(equivMonthly, sym, region.currency) + '/mo billed annually',
        strikethrough: formatMoney(monthly * 12, sym, region.currency) + '/yr',
        overageHtml: plan.overage
          ? `Covers first 100 users<br><span class="font-normal text-xs opacity-80">+ ${sym}${plan.overage} per additional user/mo</span>`
          : '',
      };
    }
    const perUserAnnual = monthlyAfterAnnualDiscount(monthly);
    return {
      main: formatMoney(perUserAnnual, sym, region.currency),
      period: '/user/mo',
      note: 'Billed annually · Save 10%',
      strikethrough: formatMoney(monthly, sym, region.currency) + '/user/mo monthly',
      overageHtml: 'Per active user · no minimum seat block',
    };
  }

  if (region.model === 'flat') {
    return {
      main: formatMoney(monthly, sym, region.currency),
      period: '/mo',
      note: '',
      strikethrough: '',
      overageHtml: plan.overage
        ? `Covers first 100 users<br><span class="font-normal text-xs opacity-80">+ ${sym}${plan.overage} per additional user</span>`
        : '',
    };
  }

  return {
    main: formatMoney(monthly, sym, region.currency),
    period: '/user/mo',
    note: '',
    strikethrough: '',
    overageHtml: 'Per active user · no minimum seat block',
  };
}

function detectDefaultRegion() {
  try {
    const saved = localStorage.getItem('aastraa_pricing_prefs');
    if (saved) {
      const p = JSON.parse(saved);
      if (p.region && PRICING[p.region]) return p.region;
    }
  } catch (_) { /* ignore */ }
  const lang = (navigator.language || 'en').toLowerCase();
  if (lang === 'en-in' || lang.endsWith('-in')) return 'IN';
  if (lang === 'en-us' || lang.endsWith('-us')) return 'US';
  if (lang === 'en-ca' || lang.endsWith('-ca')) return 'CA';
  return 'GL';
}

/** Short cross-region line under each plan card */
function getPlanIntlReference(activeRegionId, planId, billing) {
  const parts = [];
  if (activeRegionId !== 'IN') {
    const inD = getPlanPriceDisplay('IN', planId, billing);
    parts.push(`India ${inD.main}${inD.period} (100 users)`);
  }
  if (activeRegionId !== 'US' && activeRegionId !== 'GL') {
    const usD = getPlanPriceDisplay('US', planId, billing);
    parts.push(`US ${usD.main}${usD.period}`);
  }
  if (activeRegionId !== 'CA') {
    const caD = getPlanPriceDisplay('CA', planId, billing);
    parts.push(`Canada ${caD.main}${caD.period}`);
  }
  if (!parts.length) return '';
  return parts.join(' · ');
}

function getAddonIntlReference(activeRegionId, addonId) {
  const regions = ['IN', 'US', 'CA'];
  const parts = regions
    .filter((r) => r !== activeRegionId)
    .map((r) => {
      const d = getAddonPriceDisplay(r, addonId);
      if (!d) return '';
      const label = r === 'IN' ? 'India' : r === 'US' ? 'US' : 'Canada';
      return `${label} ${d.main}${d.period}`;
    })
    .filter(Boolean);
  return parts.join(' · ');
}

if (typeof window !== 'undefined') {
  window.AASTRAA_PRICING = {
    ANNUAL_DISCOUNT,
    PRICING,
    PLAN_IDS,
    PLAN_LABELS,
    ADDONS,
    COMPARISON_ROWS,
    REGION_COMPLIANCE,
    AI_CREDIT_OVERAGE,
    formatMoney,
    getAddonPriceDisplay,
    monthlyAfterAnnualDiscount,
    annualTotal,
    getPlanPriceDisplay,
    getPlanIntlReference,
    getAddonIntlReference,
    detectDefaultRegion,
  };
}
