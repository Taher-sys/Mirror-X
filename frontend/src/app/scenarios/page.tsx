import { FlaskConical } from 'lucide-react';

export default function ScenariosPage() {
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="text-center">
        <FlaskConical className="mx-auto h-16 w-16 text-zinc-700" />
        <h2 className="mt-4 text-xl font-semibold text-white">Scenario Lab</h2>
        <p className="mt-2 text-sm text-zinc-500">
          No scenarios defined. Create synthetic test scenarios to validate your system.
        </p>
      </div>
    </div>
  );
}
