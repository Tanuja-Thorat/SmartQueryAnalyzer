import React, { useEffect } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { KeyRound, Link2 } from 'lucide-react';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 280;
const nodeHeight = 300; 

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    // Estimating height based on number of columns
    const numCols = node.data.columns ? node.data.columns.length : 0;
    const estHeight = 40 + (numCols * 32); 
    dagreGraph.setNode(node.id, { width: nodeWidth, height: estHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const newNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    const newNode = {
      ...node,
      targetPosition: isHorizontal ? 'left' : 'top',
      sourcePosition: isHorizontal ? 'right' : 'bottom',
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
    return newNode;
  });

  return { nodes: newNodes, edges };
};

// Custom Node for Tables
const TableNode = ({ data }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden w-[280px]">
      <Handle type="target" position={Position.Left} className="!bg-slate-300" />
      
      <div className="bg-slate-50 border-b border-slate-200 px-3 py-2 flex items-center justify-between">
        <h3 className="font-bold text-slate-800 text-sm code-font truncate">{data.tableName}</h3>
        <span className="text-xs text-slate-500">{data.rowCount} rows</span>
      </div>
      
      <div className="flex flex-col">
        {data.columns.map((col) => {
          const isPk = data.primaryKeys.includes(col.column_name);
          const fk = data.foreignKeys.find(f => f.column_name === col.column_name);
          return (
            <div key={col.column_name} className="px-3 py-1.5 border-b border-slate-100 last:border-0 flex justify-between items-center bg-white hover:bg-slate-50 relative group">
              <div className="flex items-center gap-1.5 overflow-hidden">
                {isPk && <KeyRound className="w-3 h-3 text-amber-500 shrink-0" />}
                {fk && <Link2 className="w-3 h-3 text-blue-500 shrink-0" />}
                {!isPk && !fk && <span className="w-3 h-3 shrink-0" />}
                <span className="text-xs text-slate-700 code-font truncate" title={col.column_name}>{col.column_name}</span>
              </div>
              <span className="text-[10px] text-slate-400">{col.data_type}</span>
            </div>
          );
        })}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-slate-300" />
    </div>
  );
};

const nodeTypes = { tableNode: TableNode };

export default function ERDiagram({ schema }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!schema || schema.length === 0) return;

    const initialNodes = schema.map((table) => ({
      id: table.table_name,
      type: 'tableNode',
      data: {
        tableName: table.table_name,
        rowCount: table.row_count,
        columns: table.columns,
        primaryKeys: table.primary_keys,
        foreignKeys: table.foreign_keys,
      },
      position: { x: 0, y: 0 },
    }));

    const initialEdges = [];
    schema.forEach((table) => {
      table.foreign_keys.forEach((fk) => {
        initialEdges.push({
          id: `e-${table.table_name}-${fk.column_name}-${fk.referenced_table}`,
          source: table.table_name,
          target: fk.referenced_table,
          animated: true,
          style: { stroke: '#94a3b8', strokeWidth: 1.5 },
        });
      });
    });

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      initialNodes,
      initialEdges,
      'LR' // Left to Right layout
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [schema, setNodes, setEdges]);

  return (
    <div style={{ width: '100%', height: '600px' }} className="border border-slate-200 rounded-lg bg-slate-50 overflow-hidden relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-right"
      >
        <MiniMap />
        <Controls />
        <Background color="#cbd5e1" gap={16} />
      </ReactFlow>
    </div>
  );
}
