export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center p-8 text-center">
      <div>
        <h1 className="text-2xl font-bold">AASTRAA Careers</h1>
        <p className="text-gray-500 mt-2 text-sm">
          Visit your company careers page at <code className="bg-gray-100 px-1 rounded">/{'{tenant-slug}'}</code>
        </p>
      </div>
    </main>
  );
}
