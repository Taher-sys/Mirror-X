'use client';

import React, { useMemo, useState, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Panel,
  Node,
  Edge,
  MarkerType,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  Search,
  Filter,
  X,
  Layers,
  Database,
  Cpu,
  GitBranch,
  FileCode,
  Rocket,
  FileText,
  Table as TableIcon,
  Maximize2,
  Activity,
  ArrowRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { GraphEdge, GraphNode, GraphStatistics } from '@/lib/api';

const typeIcons: Record<string, React.ElementType> = {
  repository: GitBranch,
  service: Cpu,
  component: FileCode,
  api: Activity,
  database: Database,
  table: TableIcon,
  deployment: Rocket,
  documentation: FileText,
};

const typeColors: Record<
  string,
  { border: string; glow: string; badge: string; text: string; dot: string }
> = {
  api: {
    border: 'border-accent-cyan/80',
    glow: 'shadow-[0_0_15px_rgba(0,240,255,0.2)]',
    badge: 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/30',
    text: 'text-accent-cyan',
    dot: 'bg-accent-cyan',
  },
  service: {
    border: 'border-accent-emerald/80',
    glow: 'shadow-[0_0_15px_rgba(0,255,102,0.2)]',
    badge: 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30',
    text: 'text-accent-emerald',
    dot: 'bg-accent-emerald',
  },
  database: {
    border: 'border-purple-500/80',
    glow: 'shadow-[0_0_15px_rgba(168,85,247,0.2)]',
    badge: 'bg-purple-950/40 text-purple-400 border-purple-800/40',
    text: 'text-purple-400',
    dot: 'bg-purple-400',
  },
  table: {
    border: 'border-indigo-500/80',
    glow: 'shadow-[0_0_15px_rgba(99,102,241,0.2)]',
    badge: 'bg-indigo-950/40 text-indigo-400 border-indigo-800/40',
    text: 'text-indigo-400',
    dot: 'bg-indigo-400',
  },
  deployment: {
    border: 'border-amber-500/80',
    glow: 'shadow-[0_0_15px_rgba(245,158,11,0.2)]',
    badge: 'bg-amber-950/40 text-amber-400 border-amber-800/40',
    text: 'text-amber-400',
    dot: 'bg-amber-400',
  },
  repository: {
    border: 'border-sky-500/80',
    glow: 'shadow-[0_0_15px_rgba(14,165,233,0.2)]',
    badge: 'bg-sky-950/40 text-sky-400 border-sky-800/40',
    text: 'text-sky-400',
    dot: 'bg-sky-400',
  },
  documentation: {
    border: 'border-teal-500/80',
    glow: 'shadow-[0_0_15px_rgba(20,184,166,0.2)]',
    badge: 'bg-teal-950/40 text-teal-400 border-teal-800/40',
    text: 'text-teal-400',
    dot: 'bg-teal-400',
  },
  component: {
    border: 'border-zinc-700',
    glow: 'shadow-none',
    badge: 'bg-zinc-900 text-zinc-400 border-zinc-800',
    text: 'text-zinc-400',
    dot: 'bg-zinc-500',
  },
};

// Custom Node Component
interface CustomNodeData {
  label: string;
  nodeType: string;
  path?: string | null;
  properties?: Record<string, unknown>;
  isFocused?: boolean;
  [key: string]: unknown;
}

function RealityNodeComponent({ data }: { data: CustomNodeData }) {
  const Icon = typeIcons[data.nodeType] || Layers;
  const colors = typeColors[data.nodeType] || typeColors.component;

  return (
    <div
      className={cn(
        'group relative min-w-[190px] max-w-[250px] rounded-xl border border-white/15 border-t border-white/30 bg-zinc-900/80 p-3.5 backdrop-blur-2xl',
        'transition-all duration-300 select-none shadow-[0_8px_32px_0_rgba(0,0,0,0.6)]',
        colors.border,
        colors.glow,
        data.isFocused
          ? 'ring-2 ring-accent-cyan scale-105 shadow-[0_0_25px_rgba(0,240,255,0.4)]'
          : 'hover:-translate-y-1 hover:border-white/40 hover:shadow-[0_16px_40px_rgba(0,0,0,0.8)]'
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-2.5 !w-2.5 !rounded-full !border-white/20 !bg-[#14151a]"
      />

      <div className="flex items-center justify-between gap-2 border-b border-white/10 pb-2">
        <span
          className={cn(
            'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 font-mono text-[9px] font-bold uppercase tracking-wider border',
            colors.badge
          )}
        >
          <span className={cn('h-1.5 w-1.5 rounded-full animate-neon-pulse', colors.dot)} />
          {data.nodeType}
        </span>
        <Icon className={cn('h-3.5 w-3.5 drop-shadow-[0_0_6px_currentColor]', colors.text)} />
      </div>

      <div className="mt-2.5">
        <h4 className="font-mono text-xs font-semibold text-white tracking-tight truncate group-hover:text-cyan-300 transition-colors">
          {data.label}
        </h4>
        {data.path && (
          <p className="mt-0.5 font-mono text-[10px] text-zinc-400 truncate">
            {data.path}
          </p>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2.5 !w-2.5 !rounded-full !border-white/20 !bg-[#14151a]"
      />
    </div>
  );
}

const nodeTypes = {
  realityNode: RealityNodeComponent,
};

interface RealityGraphCanvasProps {
  initialNodes: GraphNode[];
  initialEdges: GraphEdge[];
  statistics: GraphStatistics | null;
}

export function RealityGraphCanvas({
  initialNodes,
  initialEdges,
  statistics,
}: RealityGraphCanvasProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Arrange nodes on a radial or hierarchical layout
  const rawNodes: Node<CustomNodeData>[] = useMemo(() => {
    const cols = 5;
    return initialNodes.map((n, idx) => {
      const col = idx % cols;
      const row = Math.floor(idx / cols);
      return {
        id: n.id,
        type: 'realityNode',
        position: { x: col * 260 + 50, y: row * 160 + 50 },
        data: {
          label: n.name,
          nodeType: n.node_type,
          path: n.path,
          properties: n.properties,
          isFocused: focusedNodeId === n.id,
        },
      };
    });
  }, [initialNodes, focusedNodeId]);

  const rawEdges: Edge[] = useMemo(() => {
    return initialEdges.map((e) => ({
      id: e.id,
      source: e.source_node_id,
      target: e.target_node_id,
      label: e.relationship_type,
      animated: e.relationship_type === 'calls' || e.relationship_type === 'depends_on',
      style: {
        stroke:
          e.relationship_type === 'calls'
            ? '#00F0FF'
            : e.relationship_type === 'depends_on'
            ? '#00FF66'
            : '#52525b',
        strokeWidth: 1.5,
      },
      labelStyle: {
        fill: '#a1a1aa',
        fontFamily: 'monospace',
        fontSize: 10,
        fontWeight: 500,
      },
      labelBgStyle: {
        fill: '#09090b',
        fillOpacity: 0.85,
        rx: 4,
        ry: 4,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color:
          e.relationship_type === 'calls'
            ? '#00F0FF'
            : e.relationship_type === 'depends_on'
            ? '#00FF66'
            : '#52525b',
      },
    }));
  }, [initialEdges]);

  // Filtered views
  const filteredNodes = useMemo(() => {
    return rawNodes.filter((n) => {
      const matchType = selectedType === 'all' || n.data.nodeType === selectedType;
      const matchSearch =
        !searchQuery ||
        n.data.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (n.data.path && n.data.path.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchType && matchSearch;
    });
  }, [rawNodes, selectedType, searchQuery]);

  const activeNodeIds = useMemo(
    () => new Set(filteredNodes.map((n) => n.id)),
    [filteredNodes]
  );

  const filteredEdges = useMemo(() => {
    return rawEdges.filter(
      (e) => activeNodeIds.has(e.source) && activeNodeIds.has(e.target)
    );
  }, [rawEdges, activeNodeIds]);

  const [nodes, , onNodesChange] = useNodesState(filteredNodes);
  const [edges, , onEdgesChange] = useEdgesState(filteredEdges);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const original = initialNodes.find((n) => n.id === node.id) || null;
      setSelectedNode(original);
    },
    [initialNodes]
  );

  const handleFocusNode = (nodeId: string) => {
    setFocusedNodeId((prev) => (prev === nodeId ? null : nodeId));
  };

  const types = Array.from(new Set(initialNodes.map((n) => n.node_type)));

  return (
    <div className="relative h-[calc(100vh-140px)] w-full overflow-hidden rounded-2xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 shadow-[0_20px_50px_rgba(0,0,0,0.95)] backdrop-blur-3xl">
      {/* Ambient overlay */}
      <div className="pointer-events-none absolute inset-0 z-0 bg-[#09090b]/60" />

      {/* React Flow Canvas */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
        minZoom={0.2}
        maxZoom={2.5}
        className="z-10"
      >
        <Background color="#27272a" gap={28} size={1} />
        <Controls className="!border !border-[#232736] !border-t-zinc-700/50 !bg-[#12151e]/95 !backdrop-blur-3xl !text-white !fill-white shadow-2xl rounded-xl overflow-hidden" />
        <MiniMap
          nodeColor={(n) => {
            const data = n.data as CustomNodeData;
            return typeColors[data.nodeType]?.dot ? '#f59e0b' : '#71717a';
          }}
          maskColor="rgba(9, 9, 11, 0.85)"
          className="!border !border-[#232736] !border-t-zinc-700/50 !bg-[#12151e]/95 !backdrop-blur-3xl rounded-xl overflow-hidden shadow-2xl"
        />

        {/* Top Control Bar Panel */}
        <Panel position="top-left" className="m-4 flex flex-wrap items-center gap-2.5">
          {/* Search Bar */}
          <div className="flex items-center rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 px-3.5 py-2 backdrop-blur-3xl shadow-[0_12px_32px_rgba(0,0,0,0.8)] hover:border-[#343b52] transition-colors">
            <Search className="h-3.5 w-3.5 text-zinc-400 mr-2.5" />
            <input
              type="text"
              placeholder="Search nodes or paths..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-48 bg-transparent font-sans text-xs font-bold text-white placeholder-zinc-500 outline-none"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="text-zinc-400 hover:text-white"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>

          {/* Type Filter Select */}
          <div className="flex items-center rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 px-3 py-2 backdrop-blur-3xl shadow-[0_12px_32px_rgba(0,0,0,0.8)]">
            <Filter className="h-3.5 w-3.5 text-zinc-400 mr-2" />
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-transparent font-mono text-[11px] font-bold uppercase tracking-wider text-white outline-none"
            >
              <option value="all" className="bg-[#12151e] text-white">ALL TYPES ({initialNodes.length})</option>
              {types.map((t) => (
                <option key={t} value={t} className="bg-[#12151e] text-white">
                  {t.toUpperCase()} (
                  {initialNodes.filter((n) => n.node_type === t).length})
                </option>
              ))}
            </select>
          </div>
        </Panel>

        {/* Top Right Statistics Overlay */}
        {statistics && (
          <Panel position="top-right" className="m-4">
            <div className="flex items-center gap-3.5 rounded-xl border border-[#232736] border-t border-t-zinc-700/50 bg-[#12151e]/92 px-4 py-2 font-mono text-xs font-bold backdrop-blur-3xl shadow-[0_12px_32px_rgba(0,0,0,0.8)] text-zinc-300">
              <div className="flex items-center gap-1.5">
                <span className="text-zinc-400 font-bold">NODES:</span>
                <strong className="text-white font-bold">{statistics.total_nodes}</strong>
              </div>
              <span className="text-white/20">•</span>
              <div className="flex items-center gap-1.5">
                <span className="text-zinc-400 font-bold">EDGES:</span>
                <strong className="text-amber-400 font-bold">{statistics.total_edges}</strong>
              </div>
              <span className="text-white/20">•</span>
              <div className="flex items-center gap-1.5">
                <span className="text-zinc-400 font-bold">DENSITY:</span>
                <strong className="text-amber-400 font-bold">
                  {(statistics.graph_density * 100).toFixed(1)}%
                </strong>
              </div>
            </div>
          </Panel>
        )}
      </ReactFlow>

      {/* Node Detail Sliding Drawer */}
      {selectedNode && (
        <div className="absolute right-0 top-0 bottom-0 z-30 w-80 sm:w-96 border-l border-[#232736] bg-[#12151e]/96 p-5 backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.95)] flex flex-col animate-in slide-in-from-right duration-250">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-3.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] uppercase font-bold text-amber-400 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded">
                {selectedNode.node_type}
              </span>
              <h3 className="font-mono text-xs font-bold text-white truncate max-w-[200px]">
                {selectedNode.name}
              </h3>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="rounded-lg p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto py-4 space-y-4 font-mono text-xs">
            {selectedNode.path && (
              <div>
                <span className="text-[10px] uppercase tracking-wider text-zinc-500">
                  Source Path
                </span>
                <p className="mt-0.5 text-zinc-300 break-all bg-zinc-900/60 p-2 rounded border border-zinc-800/80">
                  {selectedNode.path}
                </p>
              </div>
            )}

            {/* Properties Breakdown */}
            <div>
              <span className="text-[10px] uppercase tracking-wider text-zinc-500">
                Metadata &amp; AST Properties
              </span>
              <div className="mt-1 rounded border border-zinc-800 bg-zinc-900/60 p-2.5 space-y-1.5 text-[11px]">
                {Object.entries(selectedNode.properties).length === 0 ? (
                  <span className="text-zinc-500 italic">No extra metadata</span>
                ) : (
                  Object.entries(selectedNode.properties).map(([k, v]) => (
                    <div key={k} className="flex items-start justify-between gap-2">
                      <span className="text-zinc-500">{k}:</span>
                      <span className="text-zinc-200 break-all text-right">
                        {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Inbound & Outbound Relationships */}
            <div>
              <span className="text-[10px] uppercase tracking-wider text-zinc-500">
                Connected Relationships
              </span>
              <div className="mt-1 space-y-1.5">
                {initialEdges
                  .filter(
                    (e) =>
                      e.source_node_id === selectedNode.id ||
                      e.target_node_id === selectedNode.id
                  )
                  .map((e) => {
                    const isOutbound = e.source_node_id === selectedNode.id;
                    const otherName = isOutbound
                      ? e.target_node_name || 'Node'
                      : e.source_node_name || 'Node';
                    return (
                      <div
                        key={e.id}
                        className="flex items-center justify-between rounded border border-zinc-800 bg-zinc-900/40 p-2 text-[11px]"
                      >
                        <span className="text-accent-cyan">
                          {isOutbound ? '→ OUT' : '← IN'} [{e.relationship_type}]
                        </span>
                        <div className="flex items-center gap-1 text-zinc-300">
                          <span className="truncate max-w-[120px]">{otherName}</span>
                          <ArrowRight className="h-3 w-3 text-zinc-600" />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>

          <div className="border-t border-zinc-800 pt-3 flex items-center justify-between">
            <button
              onClick={() => handleFocusNode(selectedNode.id)}
              className="inline-flex items-center gap-1.5 rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 font-mono text-xs text-white hover:border-accent-cyan hover:text-accent-cyan transition-colors"
            >
              <Maximize2 className="h-3 w-3" />
              <span>{focusedNodeId === selectedNode.id ? 'Unfocus' : 'Focus Node'}</span>
            </button>
            <span className="font-mono text-[10px] text-zinc-500">
              ID: {selectedNode.id.slice(0, 8)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
