import { Bot } from 'lucide-react';

export default function AgentsPage() {
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="text-center">
        <Bot className="mx-auto h-16 w-16 text-zinc-700" />
        <h2 className="mt-4 text-xl font-semibold text-white">Agent Behavior Lab</h2>
        <p className="mt-2 text-sm text-zinc-500">
          No agent telemetry. Agent runs and tool calls will be visualized here.
        </p>
      </div>
    </div>
  );
}
