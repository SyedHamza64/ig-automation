// frontend/src/components/ui/BulkOperations.tsx

import { useState } from "react";

interface Account {
  id: number;
  handle: string;
  instagram_username?: string | null;
  status?: string;
}

interface BulkOperationsProps {
  accounts: Account[];
  selectedAccounts: number[];
  onSelectionChange: (selectedIds: number[]) => void;
  onBulkUpdate: (accountIds: number[], limits: any) => void;
  onBulkReset: (accountIds: number[]) => void;
  isUpdating?: boolean;
  isResetting?: boolean;
  className?: string;
}

export function BulkOperations({
  accounts,
  selectedAccounts,
  onSelectionChange,
  onBulkUpdate,
  onBulkReset,
  isUpdating = false,
  isResetting = false,
  className = ""
}: BulkOperationsProps) {
  const [showBulkForm, setShowBulkForm] = useState(false);
  const [bulkLimits, setBulkLimits] = useState({
    follow: { per_hour: 20, per_day: 100, warmup: true },
    unfollow: { per_hour: 20, per_day: 100 },
    like: { per_hour: 60, per_day: 400 },
    dm: { per_hour: 10, per_day: 50 },
    random_delay_ms: [800, 3000] as [number, number],
    block_cooldown_minutes: 60
  });

  const handleSelectAll = () => {
    if (selectedAccounts.length === accounts.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(accounts.map(acc => acc.id));
    }
  };

  const handleSelectAccount = (accountId: number) => {
    if (selectedAccounts.includes(accountId)) {
      onSelectionChange(selectedAccounts.filter(id => id !== accountId));
    } else {
      onSelectionChange([...selectedAccounts, accountId]);
    }
  };

  const handleBulkUpdate = () => {
    onBulkUpdate(selectedAccounts, bulkLimits);
    setShowBulkForm(false);
  };

  const handleBulkReset = () => {
    if (confirm(`Are you sure you want to reset limits for ${selectedAccounts.length} accounts?`)) {
      onBulkReset(selectedAccounts);
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Bulk Selection Header */}
      <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="flex items-center space-x-4">
          <button
            onClick={handleSelectAll}
            className="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            {selectedAccounts.length === accounts.length ? "Deselect All" : "Select All"}
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {selectedAccounts.length} of {accounts.length} accounts selected
          </span>
        </div>
        <div className="flex items-center space-x-2">
          {selectedAccounts.length > 0 && (
            <>
              <button
                onClick={() => setShowBulkForm(!showBulkForm)}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Bulk Update
              </button>
              <button
                onClick={handleBulkReset}
                disabled={isResetting}
                className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                {isResetting ? "Resetting..." : "Bulk Reset"}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Account Selection List */}
      <div className="max-h-64 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
        {accounts.map((account) => (
          <div
            key={account.id}
            className="flex items-center space-x-3 p-3 border-b border-gray-100 dark:border-gray-700 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-800"
          >
            <input
              type="checkbox"
              checked={selectedAccounts.includes(account.id)}
              onChange={() => handleSelectAccount(account.id)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <div className="flex-1">
              <div className="font-medium text-gray-900 dark:text-white">
                {account.handle}
              </div>
              {account.instagram_username && (
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  @{account.instagram_username}
                </div>
              )}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {account.status || "active"}
            </div>
          </div>
        ))}
      </div>

      {/* Bulk Update Form */}
      {showBulkForm && selectedAccounts.length > 0 && (
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-4">
            Bulk Update Limits for {selectedAccounts.length} Accounts
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Follow Per Hour
              </label>
              <input
                type="number"
                value={bulkLimits.follow.per_hour}
                onChange={(e) => setBulkLimits(prev => ({
                  ...prev,
                  follow: { ...prev.follow, per_hour: Number(e.target.value) }
                }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md"
                min="0"
                max="1000"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Follow Per Day
              </label>
              <input
                type="number"
                value={bulkLimits.follow.per_day}
                onChange={(e) => setBulkLimits(prev => ({
                  ...prev,
                  follow: { ...prev.follow, per_day: Number(e.target.value) }
                }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md"
                min="0"
                max="10000"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Like Per Hour
              </label>
              <input
                type="number"
                value={bulkLimits.like.per_hour}
                onChange={(e) => setBulkLimits(prev => ({
                  ...prev,
                  like: { ...prev.like, per_hour: Number(e.target.value) }
                }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md"
                min="0"
                max="1000"
              />
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={handleBulkUpdate}
              disabled={isUpdating}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isUpdating ? "Updating..." : "Apply to Selected"}
            </button>
            <button
              onClick={() => setShowBulkForm(false)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}


