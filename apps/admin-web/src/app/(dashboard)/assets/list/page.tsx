'use client';

import React, { useState } from 'react';
import { 
  Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, 
  Button, Input, Chip, Dropdown, DropdownTrigger, DropdownMenu, DropdownItem 
} from "@nextui-org/react";
import { Search, Plus, Filter, Laptop, Monitor, Mouse, MoreVertical, ShieldAlert } from 'lucide-react';

const ASSETS = [
  { id: 'AST-101', type: 'Laptop', model: 'MacBook Pro M2 14"', serial: 'C02XXXXX1', assignee: 'John Doe', status: 'Assigned', warranty: '2026-12-01' },
  { id: 'AST-102', type: 'Laptop', model: 'Dell XPS 15', serial: 'DX15-9923', assignee: 'Sarah Smith', status: 'Assigned', warranty: '2025-08-15' },
  { id: 'AST-103', type: 'Monitor', model: 'LG UltraFine 27"', serial: 'LG27-1102', assignee: 'Unassigned', status: 'Available', warranty: '2027-01-20' },
  { id: 'AST-104', type: 'Laptop', model: 'ThinkPad T14', serial: 'TP-A8810', assignee: 'Unassigned', status: 'In Repair', warranty: 'Expired' },
];

export default function AssetInventoryPage() {
  const [filterValue, setFilterValue] = useState("");

  const getIcon = (type: string) => {
    switch(type) {
      case 'Laptop': return <Laptop size={16} className="text-primary" />;
      case 'Monitor': return <Monitor size={16} className="text-secondary" />;
      default: return <Mouse size={16} className="text-default-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'Available': return 'success';
      case 'Assigned': return 'primary';
      case 'In Repair': return 'danger';
      default: return 'default';
    }
  };

  return (
    <div className="w-full flex flex-col gap-6">
      
      {/* Header */}
      <div className="flex justify-between items-center bg-content1 p-6 rounded-3xl border border-divider shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground flex items-center gap-2">
            IT Asset Inventory
          </h1>
          <p className="text-sm text-default-500 mt-1">
            Manage company hardware, assignments, and warranties.
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="flat" startContent={<Filter size={18} />}>
            Filters
          </Button>
          <Button color="primary" className="font-bold shadow-lg" startContent={<Plus size={18} />}>
            Add Asset
          </Button>
        </div>
      </div>

      {/* Data Table */}
      <div className="bg-content1 border border-divider rounded-3xl overflow-hidden p-6 shadow-sm">
        <div className="flex justify-between items-center mb-6">
          <Input
            isClearable
            className="w-full sm:max-w-[44%]"
            placeholder="Search by ID, model, or serial..."
            startContent={<Search className="text-default-300" size={18} />}
            value={filterValue}
            onClear={() => setFilterValue("")}
            onValueChange={setFilterValue}
            variant="faded"
            radius="lg"
          />
        </div>

        <Table aria-label="Assets Table" shadow="none" classNames={{ wrapper: "p-0 border-none", th: "bg-default-100 text-xs" }}>
          <TableHeader>
            <TableColumn>ASSET ID</TableColumn>
            <TableColumn>TYPE & MODEL</TableColumn>
            <TableColumn>SERIAL NUMBER</TableColumn>
            <TableColumn>ASSIGNEE</TableColumn>
            <TableColumn>WARRANTY</TableColumn>
            <TableColumn>STATUS</TableColumn>
            <TableColumn align="end">ACTIONS</TableColumn>
          </TableHeader>
          <TableBody items={ASSETS}>
            {(item) => (
              <TableRow key={item.id}>
                <TableCell className="font-bold text-primary">{item.id}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-default-100 rounded-lg">{getIcon(item.type)}</div>
                    <div className="flex flex-col">
                      <span className="font-bold text-sm">{item.model}</span>
                      <span className="text-xs text-default-500">{item.type}</span>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="font-mono text-xs text-default-600">{item.serial}</TableCell>
                <TableCell>
                  <span className={item.assignee === 'Unassigned' ? 'text-default-400 italic' : 'font-bold'}>
                    {item.assignee}
                  </span>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {item.warranty === 'Expired' && <ShieldAlert size={14} className="text-danger" />}
                    <span className={item.warranty === 'Expired' ? 'text-danger font-bold text-xs' : 'text-sm'}>
                      {item.warranty}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <Chip size="sm" variant="flat" color={getStatusColor(item.status) as any} className="font-bold">
                    {item.status}
                  </Chip>
                </TableCell>
                <TableCell>
                  <div className="flex justify-end gap-2">
                    <Dropdown placement="bottom-end">
                      <DropdownTrigger>
                        <Button isIconOnly size="sm" variant="light">
                          <MoreVertical size={16} className="text-default-500" />
                        </Button>
                      </DropdownTrigger>
                      <DropdownMenu aria-label="Asset Actions">
                        <DropdownItem key="view">View Details</DropdownItem>
                        <DropdownItem key="assign">Assign to Employee</DropdownItem>
                        <DropdownItem key="repair" color="warning">Send to Repair</DropdownItem>
                        <DropdownItem key="retire" color="danger" className="text-danger">Retire Asset</DropdownItem>
                      </DropdownMenu>
                    </Dropdown>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

    </div>
  );
}
