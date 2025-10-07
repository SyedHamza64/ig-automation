import React, { useState } from 'react';
import { useWarmupProgress, type WarmupProgress } from '../../contexts/WarmupProgressContext';

interface WarmupProgressIndicatorProps {
  className?: string;
}

const WarmupProgressIndicator: React.FC<WarmupProgressIndicatorProps> = ({ className = "" }) => {
  const { activeWarmups, removeWarmup } = useWarmupProgress();
  const [isExpanded, setIsExpanded] = useState(false);

  if (activeWarmups.length === 0) {
    return null;
  }

  const formatTime = (seconds?: number): string => {
    if (!seconds || seconds <= 0) return '0s';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  const getStatusColor = (status: WarmupProgress['status']): string => {
    switch (status) {
      case 'running': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'completed': return 'text-green-600 bg-green-50 border-green-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      case 'paused': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: WarmupProgress['status']): string => {
    switch (status) {
      case 'running': return '▶️';
      case 'completed': return '✅';
      case 'error': return '❌';
      case 'paused': return '⏸️';
      default: return '⏳';
    }
  };

  const runningWarmups = activeWarmups.filter(w => w.status === 'running');
  const completedWarmups = activeWarmups.filter(w => w.status === 'completed');
  const errorWarmups = activeWarmups.filter(w => w.status === 'error');

  return (
    <div className={`fixed bottom-4 left-4 z-50 ${className}`}>
      {/* Collapsed View */}
      {!isExpanded && (
        <div 
          className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-3 cursor-pointer hover:shadow-xl transition-all duration-200"
          onClick={() => setIsExpanded(true)}
        >
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                Warmup Active
              </span>
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {runningWarmups.length} running
              {completedWarmups.length > 0 && `, ${completedWarmups.length} done`}
              {errorWarmups.length > 0 && `, ${errorWarmups.length} failed`}
            </div>
          </div>
        </div>
      )}

      {/* Expanded View */}
      {isExpanded && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-4 max-w-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              Warmup Progress
            </h3>
            <button
              onClick={() => setIsExpanded(false)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              ✕
            </button>
          </div>

          <div className="space-y-3 max-h-64 overflow-y-auto">
            {activeWarmups.map((warmup) => (
              <div
                key={warmup.id}
                className={`p-3 rounded-lg border ${getStatusColor(warmup.status)}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm">{getStatusIcon(warmup.status)}</span>
                    <span className="text-sm font-medium truncate">
                      {warmup.accountHandle}
                    </span>
                  </div>
                  <button
                    onClick={() => removeWarmup(warmup.id)}
                    className="text-gray-400 hover:text-gray-600 text-xs"
                  >
                    ✕
                  </button>
                </div>

                {warmup.status === 'running' && (
                  <>
                    <div className="mb-2">
                      <div className="flex justify-between text-xs mb-1">
                        <span>{warmup.currentAction}</span>
                        <span>{formatTime(warmup.timeRemaining)}</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${warmup.progress}%` }}
                        ></div>
                      </div>
                    </div>
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>{Math.round(warmup.progress)}%</span>
                      <span>Duration: {formatTime(warmup.duration)}</span>
                    </div>
                  </>
                )}

                {warmup.status === 'completed' && (
                  <div className="text-xs text-green-600">
                    Completed successfully
                  </div>
                )}

                {warmup.status === 'error' && (
                  <div className="text-xs text-red-600">
                    {warmup.error || 'An error occurred'}
                  </div>
                )}

                {warmup.status === 'paused' && (
                  <div className="text-xs text-yellow-600">
                    Paused
                  </div>
                )}
              </div>
            ))}
          </div>

          {activeWarmups.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="flex justify-between text-xs text-gray-500">
                <span>Total: {activeWarmups.length}</span>
                <span>
                  Running: {runningWarmups.length} | 
                  Done: {completedWarmups.length} | 
                  Failed: {errorWarmups.length}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WarmupProgressIndicator;
