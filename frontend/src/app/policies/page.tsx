import { Shield } from 'lucide-react';

export default function PoliciesPage() {
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="text-center">
        <Shield className="mx-auto h-16 w-16 text-zinc-700" />
        <h2 className="mt-4 text-xl font-semibold text-white">Policy & Permissions</h2>
        <p className="mt-2 text-sm text-zinc-500">
          No policies configured. Define governance rules and RBAC policies here.
        </p>
      </div>
    </div>
  );
}
