import { HardDrive } from 'lucide-react';

export default function EdgePage() {
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="text-center">
        <HardDrive className="mx-auto h-16 w-16 text-zinc-700" />
        <h2 className="mt-4 text-xl font-semibold text-white">Edge Console</h2>
        <p className="mt-2 text-sm text-zinc-500">
          No edge nodes configured. Manage local-first execution nodes here.
        </p>
      </div>
    </div>
  );
}
