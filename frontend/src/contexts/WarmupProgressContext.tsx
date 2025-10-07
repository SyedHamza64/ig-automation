import React, { createContext, useContext, useState, type ReactNode } from 'react';

export interface WarmupProgress {
  id: string;
  accountId: number;
  accountHandle: string;
  profileId: number;
  status: 'running' | 'completed' | 'error' | 'paused';
  progress: number; // 0-100
  currentAction: string;
  duration: number; // total duration in seconds
  timeRemaining?: number; // in seconds
  error?: string;
  startTime: Date;
  eventSource?: EventSource;
}

interface WarmupProgressContextType {
  activeWarmups: WarmupProgress[];
  startWarmup: (accountId: number, accountHandle: string, profileId: number, duration: number, eventSource: EventSource) => string;
  updateWarmup: (id: string, updates: Partial<WarmupProgress>) => void;
  removeWarmup: (id: string) => void;
  clearAllWarmups: () => void;
  getWarmupById: (id: string) => WarmupProgress | undefined;
  getWarmupByProfileId: (profileId: number) => WarmupProgress | undefined;
}

const WarmupProgressContext = createContext<WarmupProgressContextType | undefined>(undefined);

export const useWarmupProgress = () => {
  const context = useContext(WarmupProgressContext);
  if (!context) {
    throw new Error('useWarmupProgress must be used within a WarmupProgressProvider');
  }
  return context;
};

interface WarmupProgressProviderProps {
  children: ReactNode;
}

export const WarmupProgressProvider: React.FC<WarmupProgressProviderProps> = ({ children }) => {
  const [activeWarmups, setActiveWarmups] = useState<WarmupProgress[]>([]);

  const startWarmup = (accountId: number, accountHandle: string, profileId: number, duration: number, eventSource: EventSource): string => {
    const id = `warmup-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newWarmup: WarmupProgress = {
      id,
      accountId,
      accountHandle,
      profileId,
      status: 'running',
      progress: 0,
      currentAction: 'Starting warmup...',
      duration,
      timeRemaining: duration,
      startTime: new Date(),
      eventSource,
    };
    
    setActiveWarmups(prev => [...prev, newWarmup]);
    return id;
  };

  const updateWarmup = (id: string, updates: Partial<WarmupProgress>) => {
    setActiveWarmups(prev => 
      prev.map(warmup => 
        warmup.id === id ? { ...warmup, ...updates } : warmup
      )
    );
  };

  const removeWarmup = (id: string) => {
    setActiveWarmups(prev => {
      const warmup = prev.find(w => w.id === id);
      if (warmup?.eventSource) {
        warmup.eventSource.close();
      }
      return prev.filter(w => w.id !== id);
    });
  };

  const clearAllWarmups = () => {
    setActiveWarmups([]);
  };

  const getWarmupById = (id: string): WarmupProgress | undefined => {
    return activeWarmups.find(warmup => warmup.id === id);
  };

  const getWarmupByProfileId = (profileId: number): WarmupProgress | undefined => {
    return activeWarmups.find(warmup => warmup.profileId === profileId);
  };

  const value: WarmupProgressContextType = {
    activeWarmups,
    startWarmup,
    updateWarmup,
    removeWarmup,
    clearAllWarmups,
    getWarmupById,
    getWarmupByProfileId,
  };

  return (
    <WarmupProgressContext.Provider value={value}>
      {children}
    </WarmupProgressContext.Provider>
  );
};

export default WarmupProgressProvider;
