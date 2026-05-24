'use client';

import { useState } from 'react';
import {
  Button, Card, CardBody, Chip, Input, Snippet, Spinner, Textarea,
} from '@nextui-org/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ExternalLink } from 'lucide-react';
import { JobsManager } from '@/components/recruitment/JobsManager';
import { recruitmentApi } from '@/lib/hrmsApi';

type Settings = {
  slug: string;
  api_key_prefix: string;
  logo_url: string;
  primary_color: string;
  company_blurb: string;
  allowed_embed_origins: string[];
  hosted_careers_url: string;
  embed_script_url: string;
};

export default function CareerPortalPage() {
  const queryClient = useQueryClient();
  const [newKey, setNewKey] = useState<string | null>(null);
  const [originsText, setOriginsText] = useState('');
  const [blurb, setBlurb] = useState('');
  const [color, setColor] = useState('#2563eb');
  const [logoUrl, setLogoUrl] = useState('');

  const { data: settings, isLoading, error } = useQuery({
    queryKey: ['career-portal-settings'],
    queryFn: async () => {
      const res = await recruitmentApi.careerPortal.settings();
      const s = res.data as Settings;
      setOriginsText((s.allowed_embed_origins ?? []).join('\n'));
      setBlurb(s.company_blurb ?? '');
      setColor(s.primary_color ?? '#2563eb');
      setLogoUrl(s.logo_url ?? '');
      return s;
    },
    retry: false,
  });

  const { data: snippet } = useQuery({
    queryKey: ['career-embed-snippet'],
    queryFn: async () => (await recruitmentApi.careerPortal.embedSnippet()).data as { snippet: string },
    enabled: !!settings,
  });

  const saveMutation = useMutation({
    mutationFn: () =>
      recruitmentApi.careerPortal.updateSettings({
        company_blurb: blurb,
        primary_color: color,
        logo_url: logoUrl,
        allowed_embed_origins: originsText.split('\n').map((o) => o.trim()).filter(Boolean),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['career-portal-settings'] }),
  });

  const keyMutation = useMutation({
    mutationFn: () => recruitmentApi.careerPortal.regenerateKey(),
    onSuccess: (res) => {
      setNewKey((res.data as { api_key: string }).api_key);
      queryClient.invalidateQueries({ queryKey: ['career-portal-settings'] });
    },
  });

  if (isLoading) {
    return (
      <div className="p-8 flex justify-center">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-lg">
        <h1 className="text-xl font-bold">Career board</h1>
        <p className="text-danger mt-2 text-sm">
          Job Portal add-on is not enabled for your organization. Contact your platform administrator.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="p-6 pb-0">
        <h1 className="text-2xl font-bold">Career board &amp; embed</h1>
        <p className="text-default-500 text-sm mt-1">
          Brand your hosted careers page and embed the job board on any website.
        </p>
      </div>

      <div className="px-6 grid lg:grid-cols-2 gap-4">
        <Card>
          <CardBody className="gap-4">
            <h2 className="font-semibold">Portal settings</h2>
            <Input label="Careers slug" value={settings?.slug ?? ''} isReadOnly />
            <Input label="Logo URL" value={logoUrl} onValueChange={setLogoUrl} />
            <Input label="Primary color" type="color" value={color} onValueChange={setColor} />
            <Textarea label="Company blurb" value={blurb} onValueChange={setBlurb} minRows={3} />
            <Textarea
              label="Allowed embed origins (one per line)"
              value={originsText}
              onValueChange={setOriginsText}
              minRows={3}
              placeholder="https://www.example.com"
            />
            <div className="flex gap-2 flex-wrap">
              <Button color="primary" isLoading={saveMutation.isPending} onPress={() => saveMutation.mutate()}>
                Save settings
              </Button>
              <Button variant="flat" isLoading={keyMutation.isPending} onPress={() => keyMutation.mutate()}>
                Regenerate API key
              </Button>
            </div>
            <p className="text-xs text-default-500">
              API key prefix: <Chip size="sm" variant="flat">{settings?.api_key_prefix}</Chip>
            </p>
            {newKey && (
              <Snippet symbol="" className="w-full">
                {newKey}
              </Snippet>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardBody className="gap-4">
            <h2 className="font-semibold">Links &amp; embed code</h2>
            <Button
              as="a"
              href={settings?.hosted_careers_url}
              target="_blank"
              rel="noopener noreferrer"
              variant="flat"
              startContent={<ExternalLink size={16} />}
            >
              Open hosted careers page
            </Button>
            <p className="text-xs text-default-500">Hosted URL: {settings?.hosted_careers_url}</p>
            <p className="text-sm font-medium mt-2">Embed snippet</p>
            <Snippet symbol="" className="w-full max-h-40 overflow-auto">
              {(snippet?.snippet ?? '').replace('YOUR_API_KEY', `${settings?.api_key_prefix}…`)}
            </Snippet>
            <p className="text-xs text-default-400">
              Replace YOUR_API_KEY with your full API key after regenerating.
            </p>
          </CardBody>
        </Card>
      </div>

      <JobsManager
        title="Published jobs"
        description="Publish Open requisitions to appear on your career board and embed."
        filter={{ published: 'true' }}
        showPublishActions
      />
    </div>
  );
}
