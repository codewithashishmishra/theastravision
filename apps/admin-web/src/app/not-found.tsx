'use client';

import React from 'react';
import { Button } from '@nextui-org/react';
import { MapPinOff } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

export default function NotFound() {
  const router = useRouter();

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col items-center text-center max-w-lg"
      >
        <div className="w-24 h-24 bg-primary/10 text-primary rounded-full flex items-center justify-center mb-8 shadow-inner border border-primary/20">
          <MapPinOff size={48} />
        </div>
        
        <h1 className="text-4xl font-extrabold tracking-tight mb-4">404 - Page Not Found</h1>
        
        <p className="text-default-500 text-lg mb-8">
          The module or page you are looking for doesn't exist, is currently under construction for Phase 2, or has been moved.
        </p>

        <div className="flex gap-4">
          <Button 
            color="primary" 
            size="lg" 
            className="font-bold shadow-lg shadow-primary/30"
            onPress={() => router.push('/dashboards/company')}
          >
            Go to Dashboard
          </Button>
          <Button 
            variant="flat" 
            size="lg" 
            className="font-bold"
            onPress={() => router.back()}
          >
            Go Back
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
