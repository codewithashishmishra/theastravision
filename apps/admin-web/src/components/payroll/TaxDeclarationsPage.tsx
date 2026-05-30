'use client';

import { useEffect, useState } from 'react';
import {
  Accordion,
  AccordionItem,
  Button,
  Card,
  CardBody,
  Chip,
  Input,
  Select,
  SelectItem,
  Textarea,
} from '@nextui-org/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import { payrollApi, unwrapList } from '@/lib/hrmsApi';
import { getStoredJurisdictions, type Jurisdiction } from '@/lib/jurisdiction';
import { useAuthReady } from '@/lib/AuthProvider';

type Declaration = {
  id: string;
  jurisdiction: string;
  fiscal_year: number;
  sections: Record<string, unknown>;
  status: string;
};

type TaxTip = {
  title: string;
  clause: string;
  detail: string;
  estimated_impact: string;
  action_items: string[];
};

type TaxTipsResult = {
  summary: string;
  tips: TaxTip[];
  regime_comparison?: { note: string } | null;
  disclaimer: string;
};

type CreditsResponse = {
  used: number;
  limit: number;
  remaining: number;
  period: string;
  last_tips: TaxTipsResult | null;
};

function TipsPanel({ tips }: { tips: TaxTipsResult }) {
  return (
    <div className="flex flex-col gap-4 mt-4">
      {tips.summary && (
        <p className="text-sm text-default-700 leading-relaxed">{tips.summary}</p>
      )}
      {tips.regime_comparison?.note && (
        <div className="rounded-lg bg-warning-50 border border-warning-200 p-3 text-sm text-warning-800">
          <strong>Regime comparison:</strong> {tips.regime_comparison.note}
        </div>
      )}
      {tips.tips.length > 0 && (
        <Accordion selectionMode="multiple" variant="splitted">
          {tips.tips.map((tip, idx) => (
            <AccordionItem
              key={`${tip.title}-${idx}`}
              aria-label={tip.title}
              title={
                <div className="flex flex-col gap-1">
                  <span className="font-semibold">{tip.title}</span>
                  {tip.clause && (
                    <span className="text-xs text-primary font-medium">{tip.clause}</span>
                  )}
                </div>
              }
            >
              <div className="flex flex-col gap-3 text-sm">
                <p className="text-default-700">{tip.detail}</p>
                {tip.estimated_impact && (
                  <p className="text-default-600">
                    <strong>Estimated impact:</strong> {tip.estimated_impact}
                  </p>
                )}
                {tip.action_items?.length > 0 && (
                  <ul className="list-disc pl-5 space-y-1 text-default-600">
                    {tip.action_items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                )}
              </div>
            </AccordionItem>
          ))}
        </Accordion>
      )}
      {tips.disclaimer && (
        <p className="text-xs text-default-400 italic">{tips.disclaimer}</p>
      )}
    </div>
  );
}

export function TaxDeclarationsPage() {
  const jurisdictions = getStoredJurisdictions();
  const isAuthReady = useAuthReady();
  const queryClient = useQueryClient();
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction>(jurisdictions[0] ?? 'IN');
  const [fy, setFy] = useState('2025');
  const [section80c, setSection80c] = useState('0');
  const [section80d, setSection80d] = useState('0');
  const [hraRent, setHraRent] = useState('0');
  const [taxRegime, setTaxRegime] = useState('new');
  const [tipsResult, setTipsResult] = useState<TaxTipsResult | null>(null);
  const [tipsError, setTipsError] = useState('');

  const { data: declarations } = useQuery({
    queryKey: ['tax-declarations', jurisdiction],
    enabled: isAuthReady,
    queryFn: async () => {
      const res = await api.get('/payroll/declarations/', { params: { jurisdiction } });
      return unwrapList<Declaration>(res.data);
    },
  });

  const { data: credits } = useQuery({
    queryKey: ['tax-tips-credits'],
    enabled: isAuthReady,
    queryFn: async () => {
      const res = await payrollApi.taxTips.credits();
      return res.data as CreditsResponse;
    },
  });

  useEffect(() => {
    if (credits?.last_tips) {
      setTipsResult(credits.last_tips);
    }
  }, [credits?.last_tips]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const sections =
        jurisdiction === 'IN'
          ? {
              section_80c: Number(section80c) || 0,
              section_80d: Number(section80d) || 0,
              hra_rent_paid: Number(hraRent) || 0,
              tax_regime: taxRegime,
            }
          : JSON.parse(
              `{"section_80c": ${Number(section80c) || 0}, "section_80d": ${Number(section80d) || 0}}`,
            );
      const existing = declarations?.[0];
      const payload = {
        jurisdiction,
        fiscal_year: Number(fy),
        sections,
        status: 'Submitted',
      };
      if (existing) {
        return api.put(`/payroll/declarations/${existing.id}/`, payload);
      }
      return api.post('/payroll/declarations/', payload);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tax-declarations'] }),
  });

  const tipsMutation = useMutation({
    mutationFn: async () => {
      setTipsError('');
      const res = await payrollApi.taxTips.generate({
        jurisdiction,
        fiscal_year: Number(fy),
      });
      return res.data as TaxTipsResult & CreditsResponse;
    },
    onSuccess: (data) => {
      setTipsResult({
        summary: data.summary,
        tips: data.tips ?? [],
        regime_comparison: data.regime_comparison,
        disclaimer: data.disclaimer,
      });
      queryClient.invalidateQueries({ queryKey: ['tax-tips-credits'] });
    },
    onError: (err: unknown) => {
      const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } };
      const detail = axiosErr.response?.data?.detail;
      setTipsError(
        detail ??
          (axiosErr.response?.status === 429
            ? 'Monthly AI tax tip limit reached. Try again next month.'
            : 'Failed to generate tax tips. Please try again.'),
      );
    },
  });

  const hint =
    jurisdiction === 'IN'
      ? '{"section_80c": 150000, "section_80d": 25000, "hra_rent_paid": 15000, "tax_regime": "new"}'
      : jurisdiction === 'US'
        ? '{"w4_filing_status": "single", "w4_extra_withholding": 0}'
        : '{"td1_federal_claim": 15705, "td1_provincial_claim": 11865}';

  const creditsRemaining = credits?.remaining ?? 3;
  const creditsLimit = credits?.limit ?? 3;

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      <Card className="border border-divider">
        <CardBody className="p-6 flex flex-col gap-4">
          <h1 className="text-2xl font-extrabold">Tax Declarations</h1>
          <Select
            label="Jurisdiction"
            selectedKeys={[jurisdiction]}
            onSelectionChange={(k) => setJurisdiction(String(Array.from(k)[0]) as Jurisdiction)}
          >
            {jurisdictions.map((j) => (
              <SelectItem key={j}>{j}</SelectItem>
            ))}
          </Select>
          <Input label="Fiscal / Tax Year" value={fy} onValueChange={setFy} />
          {jurisdiction === 'IN' ? (
            <>
              <Input
                type="number"
                label="Section 80C investments (₹)"
                description="PPF, ELSS, life insurance, etc. Max ₹1.5L"
                value={section80c}
                onValueChange={setSection80c}
              />
              <Input
                type="number"
                label="Section 80D health insurance (₹)"
                description="Self/family medical insurance premiums"
                value={section80d}
                onValueChange={setSection80d}
              />
              <Input
                type="number"
                label="HRA rent paid annually (₹)"
                value={hraRent}
                onValueChange={setHraRent}
              />
              <Select
                label="Tax regime"
                selectedKeys={[taxRegime]}
                onSelectionChange={(k) => setTaxRegime(String(Array.from(k)[0] ?? 'new'))}
              >
                <SelectItem key="new">New regime</SelectItem>
                <SelectItem key="old">Old regime</SelectItem>
              </Select>
            </>
          ) : (
            <Textarea
              label="Declaration details"
              value={`80C: ${section80c}, 80D: ${section80d}`}
              isReadOnly
              minRows={2}
              description="Contact payroll admin for US/CA declaration forms."
            />
          )}
          <Button color="primary" onPress={() => saveMutation.mutate()} isLoading={saveMutation.isPending}>
            Submit Declaration
          </Button>
        </CardBody>
      </Card>

      <Card className="border border-divider">
        <CardBody className="p-6 flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-extrabold">AI Tax Savings Tips</h2>
            <Chip color={creditsRemaining > 0 ? 'primary' : 'default'} variant="flat" size="sm">
              {creditsRemaining} of {creditsLimit} credits remaining this month
            </Chip>
          </div>
          <p className="text-sm text-default-500">
            Get personalized tax-saving guidance for{' '}
            {jurisdiction === 'IN' ? 'India' : jurisdiction === 'US' ? 'the United States' : 'Canada'} based on
            your salary, declarations, and payslip data.
          </p>
          <Button
            color="secondary"
            onPress={() => tipsMutation.mutate()}
            isLoading={tipsMutation.isPending}
            isDisabled={creditsRemaining <= 0}
          >
            Get AI Tax Tips
          </Button>
          {tipsError && <p className="text-sm text-danger">{tipsError}</p>}
          {tipsResult && <TipsPanel tips={tipsResult} />}
        </CardBody>
      </Card>

      <Card className="border border-divider">
        <CardBody className="p-4">
          <h2 className="font-bold mb-2">Your Declarations</h2>
          {(declarations ?? []).map((d) => (
            <div key={d.id} className="text-sm py-2 border-b border-divider">
              {d.jurisdiction} FY {d.fiscal_year} — {d.status}
            </div>
          ))}
        </CardBody>
      </Card>
    </div>
  );
}
