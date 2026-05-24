'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Users, Briefcase, Calendar, ShieldCheck, Activity } from 'lucide-react';

export default function DashboardLoading() {
  const iconVariants = {
    hidden: { opacity: 0, scale: 0.5, y: 20 },
    visible: (i: number) => ({
      opacity: 1,
      scale: 1,
      y: 0,
      transition: {
        delay: i * 0.1,
        duration: 0.5,
        repeat: Infinity,
        repeatType: 'reverse' as const,
        ease: "easeInOut"
      }
    })
  };

  const icons = [
    { Icon: Users, color: 'text-primary' },
    { Icon: Briefcase, color: 'text-secondary' },
    { Icon: Calendar, color: 'text-success' },
    { Icon: ShieldCheck, color: 'text-warning' },
    { Icon: Activity, color: 'text-danger' }
  ];

  return (
    <div className="w-full h-[60vh] flex flex-col items-center justify-center relative overflow-hidden bg-transparent">
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/10 rounded-full blur-[100px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="relative z-10 flex flex-col items-center"
      >
        <div className="flex gap-4 mb-8">
          {icons.map(({ Icon, color }, index) => (
            <motion.div
              key={index}
              custom={index}
              initial="hidden"
              animate="visible"
              variants={iconVariants}
              className={`w-14 h-14 rounded-2xl bg-content1 border border-divider shadow-lg shadow-default/10 flex items-center justify-center ${color}`}
            >
              <Icon size={24} strokeWidth={2.5} />
            </motion.div>
          ))}
        </div>

        <motion.div
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          className="flex flex-col items-center gap-2"
        >
          <h2 className="text-2xl font-black bg-gradient-to-r from-foreground to-default-500 bg-clip-text text-transparent tracking-tight">
            AastraaHR Workspace
          </h2>
          <p className="text-default-500 font-medium tracking-wide text-sm">
            Synchronizing Modules...
          </p>
        </motion.div>

        {/* Loading bar */}
        <div className="w-64 h-1.5 bg-default-100 rounded-full mt-8 overflow-hidden">
          <motion.div
            className="h-full bg-primary rounded-full"
            initial={{ width: "0%" }}
            animate={{ width: "100%" }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
        </div>
      </motion.div>
    </div>
  );
}
