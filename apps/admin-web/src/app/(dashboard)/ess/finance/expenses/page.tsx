'use client';

import React, { useState } from 'react';
import { Card, CardBody, Button, Input, Select, SelectItem, Textarea, Chip } from '@nextui-org/react';
import { Receipt, UploadCloud, Banknote, ShieldCheck } from 'lucide-react';

const MY_EXPENSES = [
  { id: 'EXP-9012', date: '2026-05-18', category: 'Travel (Flight)', amount: '$450.00', status: 'Pending Approval' },
  { id: 'EXP-8841', date: '2026-05-10', category: 'Internet Allowance', amount: '$50.00', status: 'Reimbursed' },
];

export default function ExpenseClaimsPage() {
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = () => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      alert('Expense claim submitted! It is now pending Finance approval.');
    }, 1500);
  };

  return (
    <div className="w-full flex flex-col gap-6 max-w-6xl mx-auto">
      
      {/* Header */}
      <div className="flex justify-between items-center bg-content1 p-6 rounded-3xl border border-divider shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground flex items-center gap-2">
            My Expense Claims
          </h1>
          <p className="text-sm text-default-500 mt-1">
            Submit receipts for business travel, allowances, and reimbursements.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left Col: Claim Form */}
        <Card className="shadow-sm border border-divider bg-content1">
          <CardBody className="p-8 flex flex-col gap-6">
            <h2 className="text-lg font-bold flex items-center gap-2 mb-2">
              <Banknote className="text-success" /> New Claim Request
            </h2>

            <Select label="Expense Category" variant="bordered">
              <SelectItem key="travel" value="travel">Travel (Flight/Train)</SelectItem>
              <SelectItem key="hotel" value="hotel">Accommodation (Hotel)</SelectItem>
              <SelectItem key="meals" value="meals">Client Meals & Entertainment</SelectItem>
              <SelectItem key="internet" value="internet">Monthly Internet Allowance</SelectItem>
              <SelectItem key="office" value="office">Office Supplies</SelectItem>
            </Select>

            <div className="flex gap-4">
              <Input type="number" label="Amount" placeholder="0.00" variant="bordered" className="flex-1" startContent={<span className="text-default-400">$</span>} />
              <Input type="date" label="Date of Expense" variant="bordered" className="flex-1" />
            </div>

            <Textarea 
              label="Business Justification"
              placeholder="E.g., Flight to New York for Q3 Client Summit..."
              variant="bordered"
              minRows={2}
            />

            <div className="border-2 border-dashed border-divider rounded-xl p-8 text-center hover:bg-default-50 transition-colors cursor-pointer flex flex-col items-center justify-center gap-2 bg-default-100/30 mt-2">
              <div className="p-4 bg-primary/10 rounded-full text-primary"><UploadCloud size={24} /></div>
              <p className="text-sm font-bold mt-2">Drop your receipt here</p>
              <p className="text-xs text-default-400">PDF, JPG, PNG (Max 5MB)</p>
            </div>

            <div className="flex items-start gap-3 p-4 bg-success/10 rounded-xl mt-2 border border-success/20">
              <ShieldCheck size={20} className="text-success-600 shrink-0 mt-0.5" />
              <p className="text-xs font-medium text-success-700 leading-relaxed">
                Reimbursements approved before the 25th of the month will be included in the current month's payroll cycle.
              </p>
            </div>

            <Button 
              color="primary" 
              size="lg" 
              className="font-bold shadow-lg shadow-primary/30 mt-2"
              onPress={handleSubmit}
              isLoading={isLoading}
            >
              Submit for Approval
            </Button>
          </CardBody>
        </Card>

        {/* Right Col: Past Claims */}
        <div className="flex flex-col gap-4">
          <h3 className="font-bold text-lg mb-2">Claim History</h3>
          
          {MY_EXPENSES.map((exp) => (
            <Card key={exp.id} className="shadow-sm border border-divider hover:shadow-md transition-shadow">
              <CardBody className="p-5 flex flex-row items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-default-100 rounded-xl"><Receipt className="text-default-600" size={20} /></div>
                  <div className="flex flex-col">
                    <span className="font-bold text-[15px]">{exp.category}</span>
                    <span className="text-xs text-default-500">{exp.id} • {exp.date}</span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className="font-bold text-lg text-foreground">{exp.amount}</span>
                  <Chip size="sm" variant="flat" color={exp.status === 'Reimbursed' ? 'success' : 'warning'} className="font-bold">
                    {exp.status}
                  </Chip>
                </div>
              </CardBody>
            </Card>
          ))}
          
        </div>
      </div>
    </div>
  );
}
