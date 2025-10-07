// frontend/src/pages/Limits.tsx

import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listAccounts } from "../api/accounts";
import { 
  getAccountLimits, 
  updateAccountLimits, 
  resetAccountLimits,
  type LimitsData
} from "../api/limits";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { AccountSelector, AccountInfo } from "../components/ui/AccountSelector";
import { LimitsForm } from "../components/ui/LimitsForm";
import { ChangeIndicator, SaveStatus } from "../components/ui/ChangeIndicator";
import { ActionButtons, ConfirmDialog } from "../components/ui/ActionButtons";
import { BulkOperations } from "../components/ui/BulkOperations";
import { UsageStatistics } from "../components/ui/UsageStatistics";
import { ExportImport } from "../components/ui/ExportImport";
import { LimitTemplates } from "../components/ui/LimitTemplates";
import { KeyboardShortcuts } from "../components/ui/KeyboardShortcuts";

// Simple toast helper
function toast(msg: string, type: "success" | "error" = "success") {
  console.log(`[toast:${type}]`, msg);
}

export default function LimitsPage() {
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [currentLimits, setCurrentLimits] = useState<LimitsData | null>(null);
  const [originalLimits, setOriginalLimits] = useState<LimitsData | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [selectedAccounts, setSelectedAccounts] = useState<number[]>([]);
  const [showBulkOperations, setShowBulkOperations] = useState(false);
  const [showUsageStats, setShowUsageStats] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const usageStatsRef = useRef<HTMLDivElement>(null);
  const bulkOpsRef = useRef<HTMLDivElement>(null);
  const templatesRef = useRef<HTMLDivElement>(null);

  const queryClient = useQueryClient();

  // Load accounts list
  const { data: accounts = [], isLoading: accountsLoading } = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
  });

  // Load limits for selected account
  const { 
    data: limits, 
    isLoading: limitsLoading, 
    error: limitsError 
  } = useQuery({
    queryKey: ["account-limits", selectedAccountId],
    queryFn: () => getAccountLimits(selectedAccountId!),
    enabled: !!selectedAccountId,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  });

  // Debug logging
  console.log("Limits page debug:", {
    accountsLoading,
    accounts: accounts.length,
    selectedAccountId,
    limitsLoading,
    limits: !!limits,
    currentLimits: !!currentLimits,
    limitsError
  });

  // Auto-select first account
  useEffect(() => {
    if (accounts.length > 0 && !selectedAccountId) {
      setSelectedAccountId(accounts[0].id);
    }
  }, [accounts, selectedAccountId]);

  // Update current limits when data loads or account changes
  useEffect(() => {
    if (selectedAccountId && limits) {
      console.log('Loading limits for account:', selectedAccountId, limits);
      // Create deep copies to prevent reference issues
      const limitsCopy = JSON.parse(JSON.stringify(limits));
      setCurrentLimits(limitsCopy);
      setOriginalLimits(JSON.parse(JSON.stringify(limits))); // Separate deep copy for original
      setHasChanges(false);
    } else if (selectedAccountId && !limits) {
      console.log('Account selected but no limits data yet:', selectedAccountId);
      // Clear limits when switching accounts (before new data loads)
      setCurrentLimits(null);
      setOriginalLimits(null);
      setHasChanges(false);
    }
  }, [limits, selectedAccountId]);

  // Check for changes
  useEffect(() => {
    if (currentLimits && originalLimits) {
      const changed = JSON.stringify(currentLimits) !== JSON.stringify(originalLimits);
      setHasChanges(changed);
    } else {
      setHasChanges(false);
    }
  }, [currentLimits, originalLimits]);

  // Auto-scroll to sections when shown
  useEffect(() => {
    if (showUsageStats && usageStatsRef.current) {
      setTimeout(() => {
        usageStatsRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start',
          inline: 'nearest'
        });
      }, 100);
    }
  }, [showUsageStats]);

  useEffect(() => {
    if (showBulkOperations && bulkOpsRef.current) {
      setTimeout(() => {
        bulkOpsRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start',
          inline: 'nearest'
        });
      }, 100);
    }
  }, [showBulkOperations]);

  useEffect(() => {
    if (showTemplates && templatesRef.current) {
      setTimeout(() => {
        templatesRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start',
          inline: 'nearest'
        });
      }, 100);
    }
  }, [showTemplates]);

  const selectedAccount = accounts.find(acc => acc.id === selectedAccountId);

  // Update limits mutation
  const updateLimitsMutation = useMutation({
    mutationFn: ({ accountId, limits }: { accountId: number; limits: LimitsData }) =>
      updateAccountLimits(accountId, limits),
    onSuccess: () => {
      toast("Limits updated successfully!");
      queryClient.invalidateQueries({ queryKey: ["account-limits", selectedAccountId] });
      // Create a deep copy of current limits as the new original
      setOriginalLimits(JSON.parse(JSON.stringify(currentLimits)));
      setHasChanges(false);
      setLastSaved(new Date());
    },
    onError: (error: any) => {
      toast(`Error updating limits: ${error?.response?.data?.detail || error?.message}`, "error");
    },
  });

  // Reset limits mutation
  const resetLimitsMutation = useMutation({
    mutationFn: (accountId: number) => resetAccountLimits(accountId),
    onSuccess: (message) => {
      toast(message);
      queryClient.invalidateQueries({ queryKey: ["account-limits", selectedAccountId] });
    },
    onError: (error: any) => {
      toast(`Error resetting limits: ${error?.response?.data?.detail || error?.message}`, "error");
    },
  });

  // Bulk update mutation
  const bulkUpdateMutation = useMutation({
    mutationFn: async ({ accountIds, limits }: { accountIds: number[]; limits: LimitsData }) => {
      const promises = accountIds.map(accountId => updateAccountLimits(accountId, limits));
      await Promise.all(promises);
    },
    onSuccess: () => {
      toast(`Limits updated for ${selectedAccounts.length} accounts!`);
      queryClient.invalidateQueries({ queryKey: ["account-limits"] });
      setSelectedAccounts([]);
    },
    onError: (error: any) => {
      toast(`Error updating bulk limits: ${error?.response?.data?.detail || error?.message}`, "error");
    },
  });

  // Bulk reset mutation
  const bulkResetMutation = useMutation({
    mutationFn: async (accountIds: number[]) => {
      const promises = accountIds.map(accountId => resetAccountLimits(accountId));
      await Promise.all(promises);
    },
    onSuccess: () => {
      toast(`Limits reset for ${selectedAccounts.length} accounts!`);
      queryClient.invalidateQueries({ queryKey: ["account-limits"] });
      setSelectedAccounts([]);
    },
    onError: (error: any) => {
      toast(`Error resetting bulk limits: ${error?.response?.data?.detail || error?.message}`, "error");
    },
  });

  const handleSave = () => {
    if (selectedAccountId && currentLimits) {
      updateLimitsMutation.mutate({ accountId: selectedAccountId, limits: currentLimits });
    }
  };


  const handleCancel = () => {
    if (originalLimits) {
      // Create a deep copy to prevent reference issues
      setCurrentLimits(JSON.parse(JSON.stringify(originalLimits)));
      setHasChanges(false);
    }
  };

  const handleReset = () => {
    setShowResetDialog(true);
  };

  const confirmReset = () => {
    if (selectedAccountId) {
      resetLimitsMutation.mutate(selectedAccountId);
      setShowResetDialog(false);
    }
  };

  const handleBulkUpdate = (accountIds: number[], limits: LimitsData) => {
    bulkUpdateMutation.mutate({ accountIds, limits });
  };

  const handleBulkReset = (accountIds: number[]) => {
    bulkResetMutation.mutate(accountIds);
  };

  const handleImportLimits = (limits: LimitsData) => {
    setCurrentLimits(limits);
    toast("Limits imported successfully!");
  };

  const handleApplyTemplate = (limits: LimitsData) => {
    setCurrentLimits(limits);
    toast("Template applied successfully!");
  };


  if (accountsLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Limits Management</h1>
        <div className="text-gray-500">Loading accounts...</div>
      </div>
    );
  }

  if (!accounts.length) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Limits Management</h1>
        <div className="text-gray-500">No accounts found</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Professional Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Limits Management</h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Configure rate limits and timing settings for Instagram automation
            </p>
          </div>
          
          {/* Status Indicators */}
          <div className="flex items-center space-x-4">
            <ChangeIndicator hasChanges={hasChanges} />
            <SaveStatus 
              isSaving={updateLimitsMutation.isPending} 
              lastSaved={lastSaved || undefined} 
            />
          </div>
        </div>
        
        {/* Action Buttons Row */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowBulkOperations(!showBulkOperations)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                showBulkOperations 
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' 
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Bulk Operations
            </button>
            <button
              onClick={() => setShowUsageStats(!showUsageStats)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                showUsageStats 
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' 
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Usage Statistics
            </button>
            <button
              onClick={() => setShowTemplates(!showTemplates)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                showTemplates 
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' 
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Templates
            </button>
          </div>
          
          <div className="flex items-center space-x-3">
            <KeyboardShortcuts
              onSave={handleSave}
              onCancel={handleCancel}
              onReset={handleReset}
              onToggleBulk={() => setShowBulkOperations(!showBulkOperations)}
              onToggleUsage={() => setShowUsageStats(!showUsageStats)}
              onToggleTemplates={() => setShowTemplates(!showTemplates)}
              onExport={() => {
                if (currentLimits) {
                  const dataStr = JSON.stringify(currentLimits, null, 2);
                  const dataBlob = new Blob([dataStr], { type: "application/json" });
                  const url = URL.createObjectURL(dataBlob);
                  const link = document.createElement("a");
                  link.href = url;
                  link.download = `limits-${new Date().toISOString().split("T")[0]}.json`;
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                  URL.revokeObjectURL(url);
                  toast("Limits exported successfully!");
                }
              }}
              onImport={() => {
                // Trigger file input for import
                const input = document.createElement("input");
                input.type = "file";
                input.accept = ".json";
                input.onchange = (e) => {
                  const file = (e.target as HTMLInputElement).files?.[0];
                  if (file) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                      try {
                        const content = e.target?.result as string;
                        const parsed = JSON.parse(content);
                        if (parsed.follow && parsed.unfollow && parsed.like && parsed.dm) {
                          setCurrentLimits(parsed);
                          toast("Limits imported successfully!");
                        } else {
                          toast("Invalid limits file format", "error");
                        }
                      } catch (error) {
                        toast("Error importing limits", "error");
                      }
                    };
                    reader.readAsText(file);
                  }
                };
                input.click();
              }}
              hasChanges={hasChanges}
            />
            <ActionButtons
              hasChanges={hasChanges}
              isSaving={updateLimitsMutation.isPending}
              onSave={handleSave}
              onCancel={handleCancel}
              onReset={handleReset}
              isResetting={resetLimitsMutation.isPending}
            />
          </div>
        </div>
      </div>

      {/* Account Selector */}
      <Card>
        <CardHeader title="Select Account" />
        <CardBody>
          <AccountSelector
            accounts={accounts}
            selectedAccountId={selectedAccountId}
            onAccountChange={setSelectedAccountId}
            className="max-w-md"
            showStatus={true}
          />
        </CardBody>
      </Card>

      {/* Limits Form */}
      {selectedAccountId && (
        <Card>
          <CardHeader 
            title="Account Limits"
          />
          <div className="px-6 py-2 border-b border-gray-200 dark:border-gray-700">
            <AccountInfo account={selectedAccount || null} />
          </div>
          <CardBody>
            {limitsLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600 dark:text-gray-400">Loading limits...</span>
              </div>
            ) : limitsError ? (
              <div className="text-center py-8">
                <div className="text-red-600 dark:text-red-400">
                  Error loading limits: {(limitsError as any)?.message}
                </div>
              </div>
            ) : currentLimits ? (
              <LimitsForm
                limits={currentLimits}
                onChange={setCurrentLimits}
              />
            ) : (
              <div className="text-center py-8">
                <div className="text-gray-500">
                  No limits data available
                </div>
                <div className="text-sm text-gray-400 mt-2">
                  Debug: selectedAccountId={selectedAccountId}, limits={JSON.stringify(limits)}, currentLimits={JSON.stringify(currentLimits)}
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      )}

      {/* Bulk Operations */}
      {showBulkOperations && (
        <Card ref={bulkOpsRef}>
          <CardHeader title="Bulk Operations" />
          <CardBody>
            <BulkOperations
              accounts={accounts}
              selectedAccounts={selectedAccounts}
              onSelectionChange={setSelectedAccounts}
              onBulkUpdate={handleBulkUpdate}
              onBulkReset={handleBulkReset}
              isUpdating={bulkUpdateMutation.isPending}
              isResetting={bulkResetMutation.isPending}
            />
          </CardBody>
        </Card>
      )}

      {/* Usage Statistics */}
      {showUsageStats && selectedAccountId && currentLimits && (
        <Card ref={usageStatsRef}>
          <CardHeader title="Usage Statistics" />
          <CardBody>
            <UsageStatistics
              accountId={selectedAccountId}
              limits={currentLimits}
            />
          </CardBody>
        </Card>
      )}

      {/* Export/Import */}
      {currentLimits && (
        <Card>
          <CardHeader title="Export/Import" />
          <CardBody>
            <ExportImport
              limits={currentLimits}
              onImport={handleImportLimits}
            />
          </CardBody>
        </Card>
      )}

      {/* Templates */}
      <Card ref={templatesRef}>
        <CardHeader title="Templates" />
        <CardBody>
          <LimitTemplates
            currentLimits={currentLimits || {
              follow: { per_hour: 20, per_day: 100, warmup: true },
              unfollow: { per_hour: 20, per_day: 100 },
              like: { per_hour: 60, per_day: 400 },
              dm: { per_hour: 10, per_day: 50 },
              random_delay_ms: [800, 3000],
              block_cooldown_minutes: 60
            }}
            onApplyTemplate={handleApplyTemplate}
          />
        </CardBody>
      </Card>

      {/* Confirm Reset Dialog */}
      <ConfirmDialog
        isOpen={showResetDialog}
        title="Reset Limits to Defaults"
        message="Are you sure you want to reset all limits for this account to their default values? This action cannot be undone."
        onConfirm={confirmReset}
        onCancel={() => setShowResetDialog(false)}
        type="warning"
        confirmLabel="Reset to Defaults"
      />
    </div>
  );
}
