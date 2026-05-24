'use client';

import { Tree, TreeNode } from 'react-organizational-chart';
import { OrgChartNode, type OrgChartNodeData } from './OrgChartNode';

export type OrgTreeNode = OrgChartNodeData & {
  children?: OrgTreeNode[];
};

type Props = {
  roots: OrgTreeNode[];
  searchQuery?: string;
};

function matchesSearch(node: OrgTreeNode, query: string): boolean {
  const q = query.toLowerCase();
  return (
    node.name.toLowerCase().includes(q) ||
    node.employee_code.toLowerCase().includes(q) ||
    (node.role || '').toLowerCase().includes(q) ||
    (node.designation || '').toLowerCase().includes(q)
  );
}

function nodeOrDescendantMatches(node: OrgTreeNode, query: string): boolean {
  if (!query) return false;
  if (matchesSearch(node, query)) return true;
  return (node.children || []).some((c) => nodeOrDescendantMatches(c, query));
}

function renderChildren(nodes: OrgTreeNode[], searchQuery: string) {
  return nodes.map((child) => (
    <TreeNode
      key={child.id}
      label={
        <OrgChartNode
          node={child}
          highlighted={!!searchQuery && matchesSearch(child, searchQuery)}
        />
      }
    >
      {child.children?.length ? renderChildren(child.children, searchQuery) : null}
    </TreeNode>
  ));
}

export function OrgChartTree({ roots, searchQuery = '' }: Props) {
  if (!roots.length) {
    return (
      <p className="text-center text-default-500 py-12">
        No organization hierarchy yet. Add employees and assign reporting managers.
      </p>
    );
  }

  return (
    <div className="w-full overflow-x-auto pb-8 pt-4 [&_ul]:inline-flex [&_ul]:justify-center [&_li]:list-none">
      {roots.map((root) => (
        <div key={root.id} className="mb-12 flex justify-center min-w-max px-4">
          <Tree
            lineWidth="2px"
            lineColor="var(--nextui-colors-divider)"
            lineBorderRadius="8px"
            label={
              <OrgChartNode
                node={root}
                highlighted={
                  !!searchQuery &&
                  (matchesSearch(root, searchQuery) || nodeOrDescendantMatches(root, searchQuery))
                }
              />
            }
          >
            {root.children?.length ? renderChildren(root.children, searchQuery) : null}
          </Tree>
        </div>
      ))}
    </div>
  );
}
