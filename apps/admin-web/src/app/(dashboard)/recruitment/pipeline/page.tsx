'use client';

import React, { useState } from 'react';
import { Card, CardBody, Button, Chip, Avatar } from '@nextui-org/react';
import { Search, Plus, Filter, MoreVertical, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

const STAGES = ['Sourced', 'Screening', 'Interview', 'Offer', 'Hired'];

const MOCK_CANDIDATES = [
  { id: '1', name: 'Alice Cooper', role: 'Senior Frontend Engineer', stage: 'Screening', score: 92, avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026024d' },
  { id: '2', name: 'Bob Marley', role: 'Senior Frontend Engineer', stage: 'Interview', score: 85, avatar: 'https://i.pravatar.cc/150?u=1' },
  { id: '3', name: 'Charlie Puth', role: 'Product Manager', stage: 'Offer', score: 98, avatar: 'https://i.pravatar.cc/150?u=2' },
  { id: '4', name: 'Diana Prince', role: 'UX Designer', stage: 'Sourced', score: 75, avatar: 'https://i.pravatar.cc/150?u=3' },
  { id: '5', name: 'Evan Peters', role: 'Backend Engineer', stage: 'Sourced', score: 88, avatar: 'https://i.pravatar.cc/150?u=4' },
];

export default function PipelineKanbanPage() {
  const [candidates, setCandidates] = useState(MOCK_CANDIDATES);

  const handleDragStart = (e: React.DragEvent, id: string) => {
    e.dataTransfer.setData('candidateId', id);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, stage: string) => {
    e.preventDefault();
    const id = e.dataTransfer.getData('candidateId');
    setCandidates(prev => prev.map(c => c.id === id ? { ...c, stage } : c));
  };

  return (
    <div className="w-full flex flex-col gap-6 h-[85vh]">
      
      {/* Header */}
      <div className="flex justify-between items-center bg-content1 p-6 rounded-3xl border border-divider shadow-sm shrink-0">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground flex items-center gap-2">
            Applicant Tracking Pipeline
          </h1>
          <p className="text-sm text-default-500 mt-1">
            Drag and drop candidates across stages. AI Match Scores are highlighted.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Button variant="flat" startContent={<Filter size={18} />}>
            Filter Jobs
          </Button>
          <Button color="primary" className="font-bold shadow-lg" startContent={<Plus size={18} />}>
            Add Candidate
          </Button>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="flex gap-6 overflow-x-auto pb-4 flex-1 custom-scrollbar">
        {STAGES.map(stage => {
          const stageCandidates = candidates.filter(c => c.stage === stage);
          
          return (
            <div 
              key={stage}
              className="flex-shrink-0 w-80 bg-default-50/50 border border-divider rounded-3xl flex flex-col"
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, stage)}
            >
              {/* Column Header */}
              <div className="p-5 border-b border-divider flex justify-between items-center bg-default-100/30 rounded-t-3xl">
                <h3 className="font-bold text-foreground text-lg">{stage}</h3>
                <Chip size="sm" variant="flat" className="font-bold bg-background shadow-sm">
                  {stageCandidates.length}
                </Chip>
              </div>

              {/* Candidates */}
              <div className="p-4 flex flex-col gap-4 overflow-y-auto flex-1 custom-scrollbar">
                {stageCandidates.map(candidate => (
                  <motion.div
                    layout
                    key={candidate.id}
                    draggable
                    onDragStart={(e: any) => handleDragStart(e, candidate.id)}
                  >
                    <Card className="w-full shadow-sm hover:shadow-md cursor-grab active:cursor-grabbing border border-divider">
                      <CardBody className="p-4">
                        <div className="flex justify-between items-start mb-3">
                          <Avatar src={candidate.avatar} size="sm" className="ring-2 ring-primary/20" />
                          <Button isIconOnly size="sm" variant="light" className="h-6 w-6 text-default-400">
                            <MoreVertical size={16} />
                          </Button>
                        </div>
                        <h4 className="font-bold text-[15px] leading-tight mb-1">{candidate.name}</h4>
                        <p className="text-xs text-default-500 mb-4">{candidate.role}</p>
                        
                        <div className="flex items-center justify-between mt-auto">
                          <div className={`flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-lg ${candidate.score >= 90 ? 'bg-success/10 text-success-600' : 'bg-primary/10 text-primary-600'}`}>
                            <Sparkles size={12} />
                            {candidate.score}% Match
                          </div>
                        </div>
                      </CardBody>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
