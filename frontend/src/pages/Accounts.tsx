import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { 
  listAccounts, 
  getAccountStats, 
  getRecentActions, 
  getAccountLimits,
  getLoginState,
  wsCheckProfile,
  createAccount,
  createBulkAccounts,
  getUnlinkedAccounts,
  deleteUnlinkedAccounts,
  deleteAccount,
  type AccountRow,
  type LoginState
} from "../api/accounts";
import { syncUsernamesBulk } from "../api/accounts";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { Table, TBody, TD } from "../components/ui/Table";

// Simple toast helper
function toast(msg: string) { 
  console.log("[toast]", msg); 
}

export default function AccountsPage() {
  console.log("[AccountsPage] Component rendering");
  
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const queryClient = useQueryClient();
  const [syncingAll, setSyncingAll] = useState(false);
  const [syncProgress, setSyncProgress] = useState<[number, number] | null>(null);

  // Load accounts list
  const { data: accounts = [], isLoading: accountsLoading, error: accountsError } = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
  });

  // Load unlinked accounts
  const { data: unlinkedAccounts } = useQuery({
    queryKey: ["unlinked-accounts"],
    queryFn: getUnlinkedAccounts,
    refetchInterval: 20000,
  });

  // Debug logging
  console.log("[AccountsPage] accounts:", accounts);
  console.log("[AccountsPage] accountsLoading:", accountsLoading);
  console.log("[AccountsPage] accountsError:", accountsError);

  // Auto-select first account
  useEffect(() => {
    if (accounts.length > 0 && !selectedAccountId) {
      setSelectedAccountId(accounts[0].id);
    }
  }, [accounts, selectedAccountId]);

  const selectedAccount = accounts.find(acc => acc.id === selectedAccountId);

  // Show error state if there's an error
  if (accountsError) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Accounts</h1>
        <div className="text-red-600">
          Error loading accounts: {(accountsError as any)?.message || "Unknown error"}
        </div>
        <div className="text-sm text-gray-500 mt-2">
          Check console for more details
        </div>
      </div>
    );
  }

  // Show loading state
  if (accountsLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Accounts</h1>
        <div className="text-gray-500">Loading accounts...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto p-6">
        <div className="space-y-6">
          {/* Account Management Section */}
          <Card>
        <CardHeader 
          title="Account Management" 
          subtitle={`${accounts?.length || 0} total accounts • ${unlinkedAccounts?.count || 0} unlinked`} 
        />
        <CardBody>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowCreateModal(true)}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
              >
                Create Account
              </button>
              {unlinkedAccounts?.count > 0 && (
                <DeleteUnlinkedAccountsButton />
              )}
              <button
                onClick={async () => {
                  if (syncingAll) return;
                  setSyncingAll(true);
                  setSyncProgress([0, accounts.length]);
                  try {
                    const res = await syncUsernamesBulk(accounts.map(a => a.id), 5);
                    // update cache based on results
                    queryClient.setQueryData(["accounts"], (old: any) => {
                      if (!Array.isArray(old)) return old;
                      const idToUsername = new Map<number, string>();
                      for (const r of res.results) {
                        if (r.status === 'ok' && r.instagram_username) {
                          idToUsername.set(r.id, r.instagram_username);
                        }
                      }
                      return old.map((a: any) => idToUsername.has(a.id) ? { ...a, instagram_username: idToUsername.get(a.id) } : a);
                    });
                    setSyncProgress([res.updated, res.count]);
                  } finally {
                    setTimeout(() => {
                      setSyncingAll(false);
                      setSyncProgress(null);
                    }, 400);
                  }
                }}
                disabled={syncingAll}
                className={`rounded-md px-4 py-2 text-sm text-white ${syncingAll ? 'bg-green-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600'}`}
              >
                {syncingAll && syncProgress ? `Syncing ${syncProgress[0]}/${syncProgress[1]}...` : 'Sync All Usernames'}
              </button>
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {unlinkedAccounts?.count > 0 && (
                <span className="text-yellow-600 dark:text-yellow-400">
                  ⚠️ {unlinkedAccounts.count} unlinked accounts found
                </span>
              )}
            </div>
          </div>
        </CardBody>
      </Card>

      <div className="flex h-[600px]">
        {/* Left sidebar - Account list */}
        <div className="w-80 border-r bg-gray-50 dark:bg-gray-800 flex flex-col">
          <div className="p-4 border-b dark:border-gray-700 flex-shrink-0">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Accounts ({accounts.length})</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {accounts.length === 0 ? (
              <div className="text-sm text-gray-500 dark:text-gray-400">No accounts found</div>
            ) : (
              <div className="space-y-2">
                {accounts.map((account) => (
                  <AccountListItem 
                    key={account.id} 
                    account={account} 
                    isSelected={selectedAccountId === account.id}
                    onSelect={() => setSelectedAccountId(account.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

      {/* Right pane - Account details */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6">
          {selectedAccount ? (
            <AccountDetails account={selectedAccount} />
          ) : (
            <div className="flex h-full items-center justify-center text-gray-500 dark:text-gray-400">
              <div className="text-center">
                <div className="text-4xl mb-2">👥</div>
                <div className="text-lg font-medium">Select an Account</div>
                <div className="text-sm">Choose an account from the sidebar to view details</div>
              </div>
            </div>
          )}
        </div>
      </div>
      </div>

      {/* Create Account Modal */}
      {showCreateModal && (
        <CreateAccountModal 
          onClose={() => setShowCreateModal(false)} 
          onSuccess={() => {
            setShowCreateModal(false);
            // Refresh accounts list
          }} 
        />
      )}
        </div>
      </div>
    </div>
  );
}

function AccountDetails({ account }: { account: AccountRow }) {
  const days = 14; // Show last 14 days

  // Load account data
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["acct-stats", account.id, days],
    queryFn: () => getAccountStats(account.id, days),
    refetchInterval: 20000,
  });

  const { data: recentActions, isLoading: actionsLoading } = useQuery({
    queryKey: ["acct-actions", account.id],
    queryFn: () => getRecentActions(account.id, 50),
    refetchInterval: 20000,
  });

  const { data: limits, isLoading: limitsLoading } = useQuery({
    queryKey: ["acct-limits", account.id],
    queryFn: () => getAccountLimits(account.id),
    staleTime: 20000,
  });

  // Login state (only if account has profile connections)
  const hasProfileConnection = !!account.bulk_profile_name;
  const { data: loginState } = useQuery({
    queryKey: ["login-state", account.id],
    queryFn: () => getLoginState(account.id),
    refetchInterval: 15000,
    enabled: hasProfileConnection,
  });

  // WS check (only if account has profile connections)
  const { data: wsCheck } = useQuery({
    queryKey: ["ws-check", account.id],
    queryFn: () => wsCheckProfile(account.id),
    enabled: hasProfileConnection,
  });

  // Daily counts for display
  const dailyCounts = Object.keys(stats?.likes_per_day || {})
    .sort()
    .slice(-7) // Show last 7 days
    .map(date => ({
      date,
      likes: stats?.likes_per_day?.[date] || 0,
      follows: stats?.follows_per_day?.[date] || 0,
      unfollows: stats?.unfollows_per_day?.[date] || 0,
    }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">@{account.handle}</h1>
          <div className="text-sm text-gray-500">
            Account ID: {account.id}
            {hasProfileConnection && ` • Profile: ${hasProfileConnection}`}
            {account.bulk_profile_name && (
              <div className="flex items-center gap-2 mt-1">
                <span className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700">Bulkcreate</span>
                <span className="text-xs">{account.bulk_profile_name}</span>
              </div>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {hasProfileConnection && (
            <>
              <LoginBadge state={loginState?.state} />
              <WSBadge wsCheck={wsCheck} />
            </>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          title="Today"
          value={
            statsLoading ? "..." : 
            `${stats?.today_count?.like || 0} likes, ${stats?.today_count?.follow || 0} follows`
          }
        />
        <StatCard
          title="Success Rate (7d)"
          value={statsLoading ? "..." : `${stats?.success_rate || 0}%`}
        />
        <StatCard
          title="Limits"
          value={
            limitsLoading ? "..." :
            limits?.configured ? 
              `Used: ${limits.used_today?.like || 0}/${limits.configured?.like?.per_day || 0}` :
              `Used: ${limits?.used_today?.like || 0}`
          }
        />
      </div>

      {/* Daily Counts */}
      <Card>
        <CardHeader title="Daily Activity (Last 7 Days)" />
        <CardBody>
          {statsLoading ? (
            <div className="text-sm text-gray-500">Loading...</div>
          ) : dailyCounts.length === 0 ? (
            <div className="text-sm text-gray-500">No activity in the last 7 days</div>
          ) : (
            <div className="space-y-2">
              {dailyCounts.map(({ date, likes, follows, unfollows }) => (
                <div key={date} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{date}</span>
                  <div className="flex gap-4">
                    <span className="text-red-600">{likes} likes</span>
                    <span className="text-blue-600">{follows} follows</span>
                    <span className="text-gray-600">{unfollows} unfollows</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Recent Actions */}
      <Card>
        <CardHeader title="Recent Actions" />
        <CardBody>
          {actionsLoading ? (
            <div className="text-sm text-gray-500">Loading...</div>
          ) : !recentActions || recentActions.length === 0 ? (
            <div className="text-sm text-gray-500">No recent actions</div>
          ) : (
            <Table>
              <TBody>
                {recentActions.map((action: any) => (
                  <tr key={action.id} className="border-t">
                    <TD className="text-xs text-gray-500">
                      {new Date(action.created_at).toLocaleString()}
                    </TD>
                    <TD>
                      <span className={`rounded px-2 py-0.5 text-xs ${
                        action.action_type === 'like' ? 'bg-red-100 text-red-700' :
                        action.action_type === 'follow' ? 'bg-blue-100 text-blue-700' :
                        action.action_type === 'unfollow' ? 'bg-gray-100 text-gray-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {action.action_type}
                      </span>
                    </TD>
                    <TD>
                      <span className={`rounded px-2 py-0.5 text-xs ${
                        action.status === 'success' ? 'bg-green-100 text-green-700' :
                        action.status === 'error' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {action.status}
                      </span>
                    </TD>
                    <TD className="text-sm">
                      {action.targets && action.targets.length > 0 ? 
                        action.targets.join(", ") : "—"
                      }
                    </TD>
                    <TD className="text-xs text-red-600">
                      {action.error_message || "—"}
                    </TD>
                  </tr>
                ))}
              </TBody>
            </Table>
          )}
        </CardBody>
      </Card>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: string }) {
  return (
    <Card>
      <CardBody className="space-y-1">
        <div className="text-sm text-gray-500">{title}</div>
        <div className="text-lg font-semibold">{value}</div>
      </CardBody>
    </Card>
  );
}

function LoginBadge({ state }: { state?: LoginState }) {
  const stateText = state || "unknown";
  const cls =
    stateText === "logged_in" ? "bg-green-50 text-green-700" :
    stateText === "login" ? "bg-yellow-50 text-yellow-700" :
    stateText === "error" ? "bg-red-50 text-red-700 cursor-pointer" :
    "bg-gray-50 text-gray-600";

  const handleClick = () => {
    if (stateText === "error") {
      toast("Login error: Check console for details");
    }
  };

  return (
    <span 
      className={`rounded px-2 py-0.5 text-xs ${cls}`}
      onClick={handleClick}
    >
      {stateText === "logged_in" ? "logged in" :
       stateText === "login" ? "login needed" :
       stateText === "error" ? "error" : "unknown"}
    </span>
  );
}

function WSBadge({ wsCheck }: { wsCheck?: any }) {
  if (!wsCheck) return <span className="rounded px-2 py-0.5 text-xs bg-gray-50 text-gray-600">ws unknown</span>;
  
  const isOk = wsCheck.ok === true;
  return (
    <span className={`rounded px-2 py-0.5 text-xs ${
      isOk ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
    }`}>
      {isOk ? "ws ok" : "ws fail"}
    </span>
  );
}

function AccountListItem({ account, isSelected, onSelect }: { account: AccountRow; isSelected: boolean; onSelect: () => void }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const qc = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => deleteAccount(account.id),
    onSuccess: () => {
      toast(`Account @${account.handle} deleted successfully!`);
      qc.invalidateQueries({ queryKey: ["accounts"] });
      qc.invalidateQueries({ queryKey: ["unlinked-accounts"] });
    },
    onError: (error) => {
      toast(`Error deleting account: ${error.message}`);
    }
  });

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Are you sure you want to delete account @${account.handle}? This action cannot be undone.`)) {
      return;
    }
    
    setIsDeleting(true);
    try {
      await deleteMutation.mutateAsync();
    } finally {
      setIsDeleting(false);
    }
  };

  const hasProfileConnection = !!account.bulk_profile_name;
  const isUnlinked = !hasProfileConnection;

  return (
    <div className={`rounded-lg border p-3 transition-colors ${
      isSelected
        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
        : isUnlinked
          ? "border-yellow-200 bg-yellow-50 dark:border-yellow-700 dark:bg-yellow-900/20"
          : "border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800"
    }`}>
      <div className="flex items-center justify-between">
        <button
          onClick={onSelect}
          className="flex-1 text-left"
        >
          <div className="flex items-center gap-2">
            <div className="font-medium text-gray-900 dark:text-white">@{account.handle}</div>
            {isUnlinked && (
              <span className="rounded bg-yellow-100 px-2 py-0.5 text-xs text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200">
                Unlinked
              </span>
            )}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            ID: {account.id}
            {hasProfileConnection && ` • Profile: ${hasProfileConnection}`}
            {account.instagram_username && (
              <>
                {' '}• Instagram: @{account.instagram_username}
              </>
            )}
            {account.bulk_profile_name && (
              <div className="flex items-center gap-1 mt-1">
                <span className="rounded bg-blue-50 px-1 py-0.5 text-xs text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">Bulk</span>
                <span className="text-xs">{account.bulk_profile_name}</span>
              </div>
            )}
          </div>
        </button>
        <button
          onClick={handleDelete}
          disabled={isDeleting}
          className="ml-2 rounded-md bg-red-600 px-2 py-1 text-xs text-white hover:bg-red-700 disabled:opacity-50 dark:bg-red-500 dark:hover:bg-red-600"
        >
          {isDeleting ? "..." : "×"}
        </button>
      </div>
    </div>
  );
}

function DeleteUnlinkedAccountsButton() {
  const [isDeleting, setIsDeleting] = useState(false);
  const qc = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: deleteUnlinkedAccounts,
    onSuccess: (result) => {
      toast(`Successfully deleted ${result.deleted} unlinked accounts!`);
      qc.invalidateQueries({ queryKey: ["accounts"] });
      qc.invalidateQueries({ queryKey: ["unlinked-accounts"] });
    },
    onError: (error) => {
      toast(`Error deleting accounts: ${error.message}`);
    }
  });

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete all unlinked accounts? This action cannot be undone.")) {
      return;
    }
    
    setIsDeleting(true);
    try {
      await deleteMutation.mutateAsync();
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <button
      onClick={handleDelete}
      disabled={isDeleting}
      className="rounded-md bg-red-600 px-3 py-2 text-sm text-white hover:bg-red-700 disabled:opacity-50 dark:bg-red-500 dark:hover:bg-red-600"
    >
      {isDeleting ? "Deleting..." : "Delete All Unlinked"}
    </button>
  );
}

function CreateAccountModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [handle, setHandle] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [bulkCount, setBulkCount] = useState(1);
  const [bulkPrefix, setBulkPrefix] = useState("account");
  const [creationMode, setCreationMode] = useState<'single' | 'bulk'>('single');
  const [timestamp] = useState(Date.now().toString().slice(-6));
  const qc = useQueryClient();

  const createAccountMutation = useMutation({
    mutationFn: async (data: { handle: string }) => {
      return await createAccount(data.handle);
    },
    onSuccess: () => {
      toast("Account created successfully!");
      qc.invalidateQueries({ queryKey: ["accounts"] });
      onSuccess();
    },
    onError: (error) => {
      toast(`Error creating account: ${error.message}`);
    }
  });

  const createBulkAccountsMutation = useMutation({
    mutationFn: async (data: { count: number; prefix: string }) => {
      return await createBulkAccounts(data.count, data.prefix);
    },
    onSuccess: (accounts) => {
      toast(`Successfully created ${accounts.length} accounts!`);
      qc.invalidateQueries({ queryKey: ["accounts"] });
      onSuccess();
    },
    onError: (error) => {
      toast(`Error creating accounts: ${error.message}`);
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (creationMode === 'single') {
      if (!handle.trim()) return;
      setIsCreating(true);
      try {
        await createAccountMutation.mutateAsync({ handle: handle.trim() });
      } finally {
        setIsCreating(false);
      }
    } else {
      if (bulkCount < 1 || bulkCount > 100) {
        toast("Please enter a count between 1 and 100");
        return;
      }
      setIsCreating(true);
      try {
        await createBulkAccountsMutation.mutateAsync({ count: bulkCount, prefix: bulkPrefix });
      } finally {
        setIsCreating(false);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 dark:bg-gray-800">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Create Account(s)</h2>
        
        {/* Mode Selection */}
        <div className="mb-4">
          <div className="flex rounded-md border border-gray-300 dark:border-gray-600">
            <button
              type="button"
              onClick={() => setCreationMode('single')}
              className={`flex-1 px-3 py-2 text-sm ${
                creationMode === 'single'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
              }`}
            >
              Single
            </button>
            <button
              type="button"
              onClick={() => setCreationMode('bulk')}
              className={`flex-1 px-3 py-2 text-sm ${
                creationMode === 'bulk'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
              }`}
            >
              Bulk
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {creationMode === 'single' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Account Handle
              </label>
              <input
                type="text"
                value={handle}
                onChange={(e) => setHandle(e.target.value)}
                placeholder="Enter account handle"
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                required
              />
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Number of Accounts
                </label>
                <input
                  type="number"
                  value={bulkCount}
                  onChange={(e) => setBulkCount(parseInt(e.target.value) || 1)}
                  placeholder="Enter number of accounts"
                  min="1"
                  max="100"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Prefix (e.g., "account" → account_123456_1, account_123456_2, ...)
                </label>
                <input
                  type="text"
                  value={bulkPrefix}
                  onChange={(e) => setBulkPrefix(e.target.value)}
                  placeholder="Enter prefix"
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  required
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Names will be: {bulkPrefix}_{timestamp}_1, {bulkPrefix}_{timestamp}_2, etc.
                </p>
              </div>
            </div>
          )}
          
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={isCreating}
              className="flex-1 rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
            >
              {isCreating ? "Creating..." : `Create ${creationMode === 'single' ? 'Account' : `${bulkCount} Accounts`}`}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}