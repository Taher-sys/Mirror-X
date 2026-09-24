import { Rocket } from 'lucide-react';

export default function ReleasesPage() {
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="text-center">
        <Rocket className="mx-auto h-16 w-16 text-zinc-700" />
        <h2 className="mt-4 text-xl font-semibold text-white">Release Passport</h2>
        <p className="mt-2 text-sm text-zinc-500">
          No release candidates. Create releases to track evidence, tests, and approvals.
        </p>
      </div>
    </div>
  );
}
