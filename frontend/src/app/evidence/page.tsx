import { FileCheck } from 'lucide-react';

export default function EvidencePage() {
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="text-center">
        <FileCheck className="mx-auto h-16 w-16 text-zinc-700" />
        <h2 className="mt-4 text-xl font-semibold text-white">Evidence Ledger</h2>
        <p className="mt-2 text-sm text-zinc-500">
          No evidence recorded. The immutable audit log will appear here.
        </p>
      </div>
    </div>
  );
}
