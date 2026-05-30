'use client';

/**
 * Demo voice bot — opens the public UI on the GPU voice server (ngrok).
 * Set NEXT_PUBLIC_VOICE_BOT_URL in .env.local (e.g. https://only-recant-salary.ngrok-free.dev)
 */
const VOICE_BOT_BASE =
  (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_VOICE_BOT_URL) ||
  'https://only-recant-salary.ngrok-free.dev';

export default function VoiceBotDemoPage() {
  const botUrl = `${VOICE_BOT_BASE.replace(/\/$/, '')}/bot`;

  return (
    <div style={{ padding: '1.5rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1>Astra voice demo</h1>
      <p>
        Conversational Hindi/English bot (no auth). Greeting: &quot;Hello Aashish, aapka swagat hai.&quot;
      </p>
      <p>
        <a href={botUrl} target="_blank" rel="noopener noreferrer">
          Open voice bot in new tab
        </a>
      </p>
      <iframe
        title="Astra voice demo"
        src={botUrl}
        style={{ width: '100%', height: '70vh', border: '1px solid #ccc', borderRadius: 8 }}
        allow="microphone"
      />
    </div>
  );
}
