import { Cpu } from 'lucide-react';

export default function RuntimePage() {
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="text-center">
        <Cpu className="mx-auto h-16 w-16 text-zinc-700" />
        <h2 className="mt-4 text-xl font-semibold text-white">AI Runtime</h2>
        <p className="mt-2 text-sm text-zinc-500">
          No runtime data. Monitor active models, context windows, and token usage here.
        </p>
      </div>
    </div>
  );
}
