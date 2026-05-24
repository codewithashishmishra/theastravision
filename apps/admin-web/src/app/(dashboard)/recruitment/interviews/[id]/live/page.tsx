'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardBody, Button, Chip, Avatar, Progress } from '@nextui-org/react';
import { Video, Mic, Share2, MessageSquare, Bot, User, Activity, AlertTriangle } from 'lucide-react';

const MOCK_TRANSCRIPT = [
  { sender: 'AI', text: "Hello Alice, welcome to your technical interview for the Senior Frontend Engineer role. I am Astra, your AI interviewer. Are you ready to begin?", time: "10:00 AM" },
  { sender: 'Candidate', text: "Hi Astra, yes I am ready.", time: "10:00 AM" },
  { sender: 'AI', text: "Great. Let's start with React. Can you explain the difference between Server Components and Client Components in Next.js 14?", time: "10:01 AM" },
];

export default function AIInterviewLivePage() {
  const [transcript, setTranscript] = useState(MOCK_TRANSCRIPT);
  const [isLive, setIsLive] = useState(true);
  const transcriptRef = useRef<HTMLDivElement>(null);

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcript]);

  // Simulate incoming live transcript
  useEffect(() => {
    if (!isLive) return;
    const timer = setTimeout(() => {
      setTranscript(prev => [...prev, {
        sender: 'Candidate',
        text: "Server components run exclusively on the server, which is great for fetching data securely and reducing bundle size. Client components run on the browser and are necessary when you need interactivity like onClick handlers or hooks like useState.",
        time: "10:02 AM"
      }]);
    }, 5000);

    const aiTimer = setTimeout(() => {
      setTranscript(prev => [...prev, {
        sender: 'AI',
        text: "Excellent explanation. That is highly accurate. Now, how would you handle a hydration mismatch error?",
        time: "10:02 AM"
      }]);
    }, 12000);

    return () => { clearTimeout(timer); clearTimeout(aiTimer); };
  }, [isLive]);

  return (
    <div className="w-full flex flex-col gap-6 h-[85vh]">
      
      {/* Header */}
      <div className="flex justify-between items-center bg-content1 p-4 rounded-3xl border border-divider shadow-sm shrink-0">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Avatar src="https://i.pravatar.cc/150?u=a042581f4e29026024d" size="lg" className="ring-2 ring-primary/20" />
            {isLive && <span className="absolute bottom-0 right-0 w-4 h-4 bg-danger rounded-full border-2 border-content1 animate-pulse" />}
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-foreground flex items-center gap-2">
              Alice Cooper
              <Chip size="sm" color="danger" variant="flat" className="animate-pulse font-bold ml-2">LIVE AI INTERVIEW</Chip>
            </h1>
            <p className="text-sm text-default-500 font-medium">Senior Frontend Engineer • Invited by: Recruiter</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Button variant="flat" startContent={<AlertTriangle size={18} />} color="warning">
            Flag Concern
          </Button>
          <Button color="danger" className="font-bold shadow-lg shadow-danger/30" onPress={() => setIsLive(false)}>
            Terminate Session
          </Button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="flex gap-6 flex-1 overflow-hidden">
        
        {/* Left Col: Screen Share & Video */}
        <div className="flex-[3] flex flex-col gap-6 min-w-[600px]">
          
          <Card className="flex-1 bg-black rounded-3xl overflow-hidden shadow-2xl relative border border-divider/20 group">
            <div className="absolute inset-0 flex items-center justify-center">
              {/* Simulated IDE Screen Share */}
              <div className="w-full h-full bg-[#1e1e1e] p-6 font-mono text-sm text-green-400 overflow-hidden relative">
                <div className="absolute top-0 left-0 w-full h-8 bg-[#2d2d2d] flex items-center px-4 border-b border-[#404040]">
                  <Share2 size={14} className="text-default-400 mr-2" />
                  <span className="text-default-300 text-xs">page.tsx - VS Code</span>
                </div>
                <div className="mt-10 opacity-80">
                  <p>export default function DashboardLayout() {'{'}</p>
                  <p className="pl-4 text-blue-400">const [mounted, setMounted] = useState(false);</p>
                  <p className="pl-4 text-yellow-300 mt-2">{'// Waiting for candidate input...'}</p>
                  <p>{'}'}</p>
                  {isLive && <span className="w-2 h-4 bg-white inline-block animate-pulse mt-2 ml-4" />}
                </div>
              </div>
            </div>
            
            {/* Candidate PIP Video */}
            <div className="absolute bottom-6 left-6 w-64 aspect-video bg-content2 rounded-xl overflow-hidden border-2 border-divider shadow-2xl group-hover:scale-105 transition-transform z-10">
               <img src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=600&auto=format&fit=crop" alt="Candidate Feed" className="w-full h-full object-cover" />
               <div className="absolute bottom-2 left-2 bg-black/60 px-2 py-1 rounded text-xs text-white flex items-center gap-2 backdrop-blur-md">
                 <Mic size={12} className="text-success animate-pulse" />
                 Alice Cooper
               </div>
            </div>

            <div className="absolute top-6 right-6 flex gap-2">
               <div className="bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-lg text-xs font-bold text-white flex items-center gap-2">
                 <Activity size={14} className="text-danger" /> 32ms Latency
               </div>
            </div>
          </Card>
        </div>

        {/* Right Col: Live Transcript & AI Analysis */}
        <div className="flex-[2] flex flex-col gap-6 min-w-[400px]">
          
          <Card className="flex-1 shadow-sm border border-divider flex flex-col">
            <div className="p-4 border-b border-divider bg-default-50/50 flex justify-between items-center shrink-0">
              <h3 className="font-bold flex items-center gap-2">
                <MessageSquare size={18} className="text-primary"/> Live Transcript
              </h3>
              <Chip size="sm" variant="flat" color="success">Recording Active</Chip>
            </div>
            
            <CardBody className="p-6 flex flex-col gap-4 overflow-y-auto custom-scrollbar" ref={transcriptRef}>
              {transcript.map((msg, i) => (
                <div key={i} className={`flex gap-3 max-w-[90%] ${msg.sender === 'Candidate' ? 'ml-auto flex-row-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.sender === 'AI' ? 'bg-primary/20 text-primary' : 'bg-success/20 text-success'}`}>
                    {msg.sender === 'AI' ? <Bot size={16} /> : <User size={16} />}
                  </div>
                  <div className={`flex flex-col ${msg.sender === 'Candidate' ? 'items-end' : ''}`}>
                    <span className="text-[11px] text-default-400 font-medium mb-1 px-1">{msg.sender} • {msg.time}</span>
                    <div className={`p-3 rounded-2xl text-[14px] leading-relaxed shadow-sm ${msg.sender === 'Candidate' ? 'bg-content2 text-foreground border border-divider' : 'bg-primary/10 text-primary-800 border border-primary/20'}`}>
                      {msg.text}
                    </div>
                  </div>
                </div>
              ))}
            </CardBody>
          </Card>

          <Card className="shrink-0 shadow-sm border border-divider bg-content1">
            <CardBody className="p-6">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <Bot size={18} className="text-secondary"/> Live AI Sentiment Analysis
              </h3>
              <div className="flex flex-col gap-4">
                <div>
                  <div className="flex justify-between text-xs font-bold text-default-600 mb-1">
                    <span>Technical Accuracy Confidence</span>
                    <span className="text-success">92%</span>
                  </div>
                  <Progress value={92} color="success" size="sm" />
                </div>
                <div>
                  <div className="flex justify-between text-xs font-bold text-default-600 mb-1">
                    <span>Communication Clarity</span>
                    <span className="text-primary">85%</span>
                  </div>
                  <Progress value={85} color="primary" size="sm" />
                </div>
              </div>
            </CardBody>
          </Card>

        </div>
      </div>

    </div>
  );
}
