import React, { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listProfiles, getLoginState, listBulkcreateProfiles, attachBulkProfile, startWarmupStream } from "../api/profiles";
import { listAccounts, createAccount, createBulkAccounts, getUnlinkedAccounts, deleteAccount, detectOrphanedLinks, cleanupOrphanedLinks, cleanupSelectedOrphanedLinks, updateAutoCleanupSettings, type AccountRow } from "../api/accounts";
import { Card, CardBody, CardHeader } from "../components/ui/Card";

type Tab = "linked" | "unlinked" | "all" | "bulkcreate" | "accounts";

// Simple toast helper (non-blocking)
function toast(msg: string) { 
  console.log("[toast]", msg); 
}

export default function ProfilesPage() {
  const { isLoading, isError, isFetching } = useQuery({
    queryKey: ["profiles"],
    queryFn: listProfiles,
    refetchInterval: 20000, // auto-refresh list
  });

  const { data: accounts, isLoading: accountsLoading } = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
    refetchInterval: 20000,
  });

  const { data: unlinkedAccounts, isLoading: unlinkedLoading } = useQuery({
    queryKey: ["unlinked-accounts"],
    queryFn: getUnlinkedAccounts,
    refetchInterval: 20000,
  });

  const { data: bulkcreateProfiles, isLoading: bulkcreateLoading, isFetching: bulkcreateFetching } = useQuery({
    queryKey: ["bulkcreate-profiles"],
    queryFn: listBulkcreateProfiles,
    refetchInterval: 30000, // auto-refresh bulkcreate profiles
  });

  const [tab, setTab] = useState<Tab>("linked");
  const [q, setQ] = useState("");
  const [showCreateAccount, setShowCreateAccount] = useState(false);
  const [showLinkProfile, setShowLinkProfile] = useState(false);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);

  
  // Delete account mutation
  const queryClient = useQueryClient();
  
  const deleteAccountMutation = useMutation({
    mutationFn: (accountId: number) => deleteAccount(accountId),
    onSuccess: () => {
      toast("Account deleted successfully!");
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      queryClient.invalidateQueries({ queryKey: ["unlinked-accounts"] });
    },
    onError: (error) => {
      toast(`Error deleting account: ${error.message}`);
    }
  });
  
  // Since we've merged profiles into accounts, use account data for counts
  const accountRows = accounts || [];
  
  const counts = useMemo(() => {
    const linked = accountRows.filter((r) => !!r.bulk_profile_name || !!r.adspower_profile_id).length;
    const bulkcreate = accountRows.filter((r) => !!r.bulk_profile_name).length;
    const adspower = accountRows.filter((r) => !!r.adspower_profile_id).length;
    return { total: accountRows.length, linked, unlinked: accountRows.length - linked, bulkcreate, adspower };
  }, [accountRows]);

  // Collect all errors from login state queries
  const [errors, setErrors] = useState<Array<{id: number, error: string, adspower_id: string | null, account_handle?: string}>>([]);

  const handleError = (id: number, error: string) => {
    console.log(`[DEBUG] Error detected for profile ${id}:`, error);
    const account = accountRows.find((r: any) => r.id === id);
    if (account) {
      setErrors(prev => {
        const existing = prev.find(e => e.id === id);
        if (existing) {
          return prev.map(e => e.id === id ? { ...e, error } : e);
        } else {
          return [...prev, { 
            id, 
            error, 
            adspower_id: account.adspower_profile_id || null,
            account_handle: account.handle || undefined
          }];
        }
      });
    }
  };

  const filtered = useMemo(() => {
    let r = accountRows;
    if (tab === "linked") r = r.filter((x) => !!x.bulk_profile_name || !!x.adspower_profile_id);
    if (tab === "unlinked") r = r.filter((x) => !x.bulk_profile_name && !x.adspower_profile_id);
    if (tab === "bulkcreate") r = r.filter((x) => !!x.bulk_profile_name);
    if (q.trim()) {
      const s = q.trim().toLowerCase();
      r = r.filter(
        (x) =>
          x.adspower_profile_id?.toLowerCase().includes(s) ||
          x.bulk_profile_name?.toLowerCase().includes(s) ||
          x.handle?.toLowerCase().includes(s)
      );
    }
    return r;
  }, [accountRows, tab, q]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto p-6">
    <div className="space-y-6">
      {/* Top summary + controls */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-6">
        <Stat title="Total" value={counts.total} />
        <Stat title="Linked" value={counts.linked} />
        <Stat title="Unlinked" value={counts.unlinked} />
            <Stat title="Bulkcreate" value={counts.bulkcreate} />
            <Stat title="AdsPower" value={counts.adspower} />
            <div className="flex items-end justify-end gap-2">
          <button
                onClick={() => setShowCreateAccount(true)}
                className="rounded-md bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
              >
                Create Account
              </button>
              <button
                onClick={() => setShowLinkProfile(true)}
                className="rounded-md bg-green-600 px-3 py-2 text-sm text-white hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600"
              >
                Link Profile
          </button>
        </div>
      </div>

      {/* Create Account Modal */}
      {showCreateAccount && (
        <CreateAccountModal
          onClose={() => setShowCreateAccount(false)}
          onSuccess={() => {
            setShowCreateAccount(false);
            toast("Account created successfully!");
          }}
        />
      )}

      {/* Link Profile Modal */}
      {showLinkProfile && (
        <LinkProfileModal
          accounts={accounts || []}
          bulkcreateProfiles={bulkcreateProfiles || {}}
          onClose={() => setShowLinkProfile(false)}
          onSuccess={() => {
            setShowLinkProfile(false);
            toast("Profile linked successfully!");
          }}
        />
      )}

      {/* Bulkcreate Available Profiles */}
      {tab === "bulkcreate" && bulkcreateProfiles && (
        <Card>
          <CardHeader 
            title="Available Bulkcreate Profiles" 
            subtitle={`${Object.keys(bulkcreateProfiles).length} profiles available ${bulkcreateFetching ? '• Refreshing...' : ''}`}
          />
          <CardBody>
            {bulkcreateLoading ? (
              <div className="py-4 text-sm text-gray-500">Loading bulkcreate profiles...</div>
            ) : (
              <BulkcreateProfileManager 
                bulkcreateProfiles={bulkcreateProfiles}
                accounts={accounts || []}
              />
            )}
          </CardBody>
        </Card>
      )}

      {/* Accounts Tab */}
      {tab === "accounts" && (
        <div className="space-y-6">
          {/* Top Section: Quick Stats and Actions */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            {/* Account Stats */}
            <Card>
              <CardHeader title="Account Overview" />
          <CardBody>
            <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Total:</span>
                    <span className="font-medium text-lg">{accounts?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Linked:</span>
                    <span className="font-medium text-green-600 dark:text-green-400">{(accounts?.length || 0) - (unlinkedAccounts?.count || 0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Unlinked:</span>
                    <span className="font-medium text-yellow-600 dark:text-yellow-400">{unlinkedAccounts?.count || 0}</span>
                  </div>
                </div>
              </CardBody>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader title="Quick Actions" />
              <CardBody>
                <div className="space-y-2">
                  <button
                    onClick={() => setShowCreateAccount(true)}
                    className="w-full rounded-md bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
                  >
                    Create Account
                  </button>
                  {unlinkedAccounts?.count > 0 && (
                    <DeleteUnlinkedAccountsButton />
                  )}
                </div>
              </CardBody>
            </Card>

            {/* Orphaned Links Manager */}
            <Card className="lg:col-span-2">
              <CardHeader title="Orphaned Links Management" />
              <CardBody>
                {accounts && accounts.length > 0 && <OrphanedLinksManager accounts={accounts} />}
              </CardBody>
            </Card>
          </div>

          {/* Main Content: Accounts List and Details */}
          <div className="space-y-6">
            {/* Accounts List */}
            <div>
              <Card>
                <CardHeader 
                  title={`All Accounts (${accounts?.length || 0})`} 
                  subtitle={`${unlinkedAccounts?.count || 0} unlinked • ${(accounts?.length || 0) - (unlinkedAccounts?.count || 0)} linked`}
                />
                <CardBody>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {accountsLoading || unlinkedLoading ? (
                      <div className="py-4 text-sm text-gray-500">Loading accounts...</div>
                    ) : !accounts || accounts.length === 0 ? (
                      <div className="py-4 text-sm text-gray-500">No accounts found</div>
                    ) : (
                      accounts.map((account) => (
                        <AccountSidebarItem 
                          key={account.id} 
                          account={account} 
                          isSelected={selectedAccountId === account.id}
                          onSelect={() => setSelectedAccountId(account.id)}
                          onDelete={() => {
                            if (confirm(`Are you sure you want to delete account ${account.handle}?`)) {
                              deleteAccountMutation.mutate(account.id);
                            }
                          }}
                        />
                      ))
                    )}
                  </div>
                </CardBody>
              </Card>
            </div>

            {/* Account Details */}
            <div>
              <Card>
                <CardHeader title="Account Details" />
                <CardBody>
                  {selectedAccountId ? (
                    <AccountDetails 
                      account={accounts?.find(acc => acc.id === selectedAccountId)} 
                      onClose={() => setSelectedAccountId(null)}
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 text-gray-500 dark:text-gray-400">
                      <div className="w-16 h-16 mb-4 text-purple-500">
                        <svg className="w-full h-full" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-medium mb-2">Select an Account</h3>
                      <p className="text-sm text-center">Choose an account from the sidebar to view details</p>
                    </div>
                  )}
                </CardBody>
              </Card>
            </div>
          </div>
        </div>
      )}

      {/* Error Section - Fixed height and scrollable */}
      {errors.length > 0 && (
        <Card>
          <CardHeader title="Errors" subtitle={`${errors.length} profile(s) with errors (showing latest 10)`} />
          <CardBody>
            <div className="h-48 overflow-y-auto space-y-2">
              {errors.slice(0, 10).map((err) => (
                <div key={err.id} className="flex items-center justify-between rounded-md bg-red-50 p-3 dark:bg-red-900/20">
                  <div className="flex items-center gap-3">
                    <code className="text-xs text-red-600 dark:text-red-400">{err.adspower_id}</code>
                    {err.account_handle && (
                      <span className="text-sm text-red-700 dark:text-red-300">@{err.account_handle}</span>
                    )}
                    <span className="text-sm text-red-600 dark:text-red-400">{err.error}</span>
                  </div>
                  <button
                    onClick={() => setErrors(prev => prev.filter(e => e.id !== err.id))}
                    className="text-xs text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                  >
                    ✕
                  </button>
                </div>
              ))}
              {errors.length > 10 && (
                <div className="text-center text-sm text-gray-500 dark:text-gray-400 py-2">
                  ... and {errors.length - 10} more errors
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Tabs + Search */}
      <Card>
        <CardHeader 
          title="Profiles" 
          subtitle={`Linked / Unlinked / Bulkcreate / Accounts / All ${isFetching ? '• Refreshing...' : ''}`} 
        />
        <CardBody>
          <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="inline-flex overflow-hidden rounded-md border">
              <TabBtn active={tab === "linked"} onClick={() => setTab("linked")}>
                Linked
              </TabBtn>
              <TabBtn active={tab === "unlinked"} onClick={() => setTab("unlinked")}>
                Unlinked
              </TabBtn>
              <TabBtn active={tab === "bulkcreate"} onClick={() => setTab("bulkcreate")}>
                Bulkcreate
              </TabBtn>
              <TabBtn active={tab === "accounts"} onClick={() => setTab("accounts")}>
                Accounts
              </TabBtn>
              <TabBtn active={tab === "all"} onClick={() => setTab("all")}>
                All
              </TabBtn>
            </div>
            <input
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 sm:w-64 placeholder-gray-500 dark:placeholder-gray-400"
              placeholder="Search by profile ID, account, or bulkcreate name…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>

          {/* List - Fixed height with scrolling */}
          <div className="h-[600px] overflow-y-auto">
          {isLoading ? (
              <div className="py-8 text-sm text-gray-500 dark:text-gray-400">Loading…</div>
          ) : isError ? (
              <div className="py-8 text-sm text-red-600 dark:text-red-400">Failed to load profiles.</div>
          ) : filtered.length === 0 ? (
              <div className="py-8 text-sm text-gray-500 dark:text-gray-400">No profiles.</div>
          ) : (
              <div className="space-y-2 p-1">
              {filtered.map((p) => (
                  <AccountRowItem key={p.id} account={p} onError={handleError} />
              ))}
            </div>
          )}
          </div>
        </CardBody>
      </Card>
        </div>
      </div>
    </div>
  );
}

function DeleteUnlinkedAccountsButton() {
  const [isDeleting, setIsDeleting] = useState(false);
  const qc = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: async () => {
      // Get unlinked accounts first
      const unlinkedResponse = await getUnlinkedAccounts();
      const unlinkedAccounts = unlinkedResponse.accounts || [];
      
      if (unlinkedAccounts.length === 0) {
        return { deleted: 0, message: "No unlinked accounts found" };
      }
      
      // Delete accounts individually
      let deletedCount = 0;
      const deletedAccounts = [];
      
      for (const account of unlinkedAccounts) {
        try {
          await deleteAccount(account.id);
          deletedCount++;
          deletedAccounts.push(account);
        } catch (error) {
          console.warn(`Failed to delete account ${account.id}:`, error);
          // Continue with other accounts
        }
      }
      
      return {
        deleted: deletedCount,
        accounts: deletedAccounts,
        message: `Successfully deleted ${deletedCount} out of ${unlinkedAccounts.length} unlinked accounts. Note: Unused profiles remain in database and can be cleaned up separately.`
      };
    },
    onSuccess: (result) => {
      toast(result.message);
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
  const qc = useQueryClient();

  const [bulkCount, setBulkCount] = useState(1);
  const [bulkPrefix, setBulkPrefix] = useState("account");
  const [creationMode, setCreationMode] = useState<'single' | 'bulk'>('single');
  const [timestamp] = useState(Date.now().toString().slice(-6));

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
      <div className="w-full max-w-md rounded-lg bg-white dark:bg-gray-800 p-6 border border-gray-200 dark:border-gray-700">
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

function LinkProfileModal({ 
  accounts, 
  bulkcreateProfiles, 
  onClose, 
  onSuccess 
}: { 
  accounts: AccountRow[]; 
  bulkcreateProfiles: Record<string, any>; 
  onClose: () => void; 
  onSuccess: () => void; 
}) {
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<string>("");
  const [isLinking, setIsLinking] = useState(false);
  const qc = useQueryClient();

  const linkProfileMutation = useMutation({
    mutationFn: async (data: { accountId: number; profileName: string }) => {
      return await attachBulkProfile(data.profileName, data.accountId);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profiles"] });
      qc.invalidateQueries({ queryKey: ["accounts"] });
      onSuccess();
    },
    onError: (error) => {
      toast(`Error: ${error.message}`);
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAccount || !selectedProfile) return;
    
    setIsLinking(true);
    try {
      await linkProfileMutation.mutateAsync({ 
        accountId: selectedAccount, 
        profileName: selectedProfile 
      });
    } finally {
      setIsLinking(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="w-full max-w-md rounded-lg bg-white dark:bg-gray-800 p-6 border border-gray-200 dark:border-gray-700">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Link Profile to Account</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Select Account</label>
            <select
              value={selectedAccount || ""}
              onChange={(e) => setSelectedAccount(Number(e.target.value))}
              className="mt-1 w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2"
              required
            >
              <option value="">Choose an account...</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  @{account.handle} (ID: {account.id})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Select Bulkcreate Profile</label>
            <select
              value={selectedProfile}
              onChange={(e) => setSelectedProfile(e.target.value)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2"
              required
            >
              <option value="">Choose a profile...</option>
              {Object.entries(bulkcreateProfiles).map(([name, profile]: [string, any]) => (
                <option key={name} value={name}>
                  {name} ({profile.enhancedMode ? 'Enhanced' : 'Standard'})
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLinking}
              className="rounded-md bg-green-600 px-3 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-50"
            >
              {isLinking ? "Linking..." : "Link Profile"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


function TabBtn({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
        active 
          ? "bg-blue-100 text-blue-700 font-medium dark:bg-blue-900/30 dark:text-blue-300" 
          : "bg-white hover:bg-gray-50 text-gray-700 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-300"
      }`}
    >
      {children}
    </button>
  );
}

function Stat({ title, value }: { title: string; value: number | string }) {
  return (
    <Card>
      <CardBody className="space-y-1">
        <div className="text-sm text-gray-500 dark:text-gray-400">{title}</div>
        <div className="text-2xl font-semibold text-gray-900 dark:text-white">{value}</div>
      </CardBody>
    </Card>
  );
}

function HealthBadge({ value }: { value?: string | null }) {
  const v = (value || "unknown").toLowerCase();
  const cls =
    v === "ok"
      ? "bg-green-50 text-green-700"
      : v === "error"
      ? "bg-red-50 text-red-700"
      : "bg-gray-50 text-gray-600";
  return <span className={`rounded px-2 py-0.5 text-xs ${cls}`}>{v}</span>;
}

function LoginBadge({ id, onError }: { id: number, onError?: (id: number, error: string) => void }) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["login-state", id],
    queryFn: () => getLoginState(id),
    enabled: !!id,
    refetchInterval: false,
    refetchOnWindowFocus: false,
    staleTime: 60000,
  });
  const state = data?.state ?? (isError ? "error" : isLoading ? "…" : "unknown");
  const cls =
    state === "logged_in" ? "bg-green-50 text-green-700" :
    state === "login"     ? "bg-yellow-50 text-yellow-700" :
    state === "error"     ? "bg-red-50 text-red-700" :
                            "bg-gray-50 text-gray-600";
  
  // Report errors to parent (both data-level and query-level errors)
  React.useEffect(() => {
    console.log(`[DEBUG] LoginBadge ${id}: state=${state}, isError=${isError}, error=`, error);
    if (onError) {
      if (state === "error") {
        const errorMsg = error?.message || "Unknown error";
        console.log(`[DEBUG] Reporting data-level error for ${id}:`, errorMsg);
        onError(id, errorMsg);
      } else if (isError && error) {
        // Handle query-level errors (like 502 responses)
        const errorMsg = (error as any)?.response?.data?.detail || error?.message || "Connection failed";
        console.log(`[DEBUG] Reporting query-level error for ${id}:`, errorMsg);
        onError(id, errorMsg);
      }
    }
  }, [state, isError, error, id, onError]);

  return (
    <span className={`rounded px-2 py-0.5 text-xs ${cls}`}>
      {state}
    </span>
  );
}


function BulkcreateProfileManager({ 
  bulkcreateProfiles, 
  accounts 
}: { 
  bulkcreateProfiles: Record<string, any>; 
  accounts: AccountRow[]; 
}) {
  const [selectedProfiles, setSelectedProfiles] = useState<Set<string>>(new Set());
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null);
  const [isLinking, setIsLinking] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [linkMode, setLinkMode] = useState<'manual' | 'auto'>('auto');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const qc = useQueryClient();
  
  const profileEntries = Object.entries(bulkcreateProfiles);
  const linkedProfiles = new Set(accounts.filter(account => account.bulk_profile_name).map(account => account.bulk_profile_name));
  
  // Filter profiles based on search
  const filteredProfiles = profileEntries.filter(([name, profile]) => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return name.toLowerCase().includes(search) || 
           (profile.user_agent || '').toLowerCase().includes(search);
  });

  const unlinkedProfiles = filteredProfiles.filter(([name]) => !linkedProfiles.has(name));
  const linkedProfilesList = filteredProfiles.filter(([name]) => linkedProfiles.has(name));
  const linkedCount = linkedProfilesList.length;

  // Get available accounts (those without profiles)
  const availableAccounts = accounts.filter(account => !account.bulk_profile_name && !account.adspower_profile_id);
  const availableAccountsCount = availableAccounts.length;

  // Create a map of bulk profile names to their linked account info
  const profileToAccountMap = new Map<string, { id: number; handle: string }>();
  accounts.forEach(account => {
    if (account.bulk_profile_name) {
      profileToAccountMap.set(account.bulk_profile_name, {
        id: account.id,
        handle: account.handle
      });
    }
  });

  const handleSelectAll = () => {
    if (selectedProfiles.size === unlinkedProfiles.length) {
      setSelectedProfiles(new Set());
    } else {
      setSelectedProfiles(new Set(unlinkedProfiles.map(([name]) => name)));
    }
  };

  const handleSelectAllLinked = () => {
    if (selectedProfiles.size === linkedProfilesList.length) {
      setSelectedProfiles(new Set());
    } else {
      setSelectedProfiles(new Set(linkedProfilesList.map(([name]) => name)));
    }
  };

  const handleProfileSelect = (profileName: string) => {
    const newSelected = new Set(selectedProfiles);
    if (newSelected.has(profileName)) {
      newSelected.delete(profileName);
    } else {
      newSelected.add(profileName);
    }
    setSelectedProfiles(newSelected);
    // Clear error message when selection changes
    if (errorMessage) {
      setErrorMessage(null);
    }
  };

  const linkSelectedProfiles = async () => {
    if (selectedProfiles.size === 0) return;
    
    // Filter to only unlinked profiles
    const selectedUnlinkedProfiles = Array.from(selectedProfiles).filter(name => !linkedProfiles.has(name));
    
    if (selectedUnlinkedProfiles.length === 0) {
      toast("No unlinked profiles selected for linking");
      return;
    }

    // For auto mode, check if we have enough available accounts
    if (linkMode === 'auto' && availableAccountsCount < selectedUnlinkedProfiles.length) {
      setErrorMessage(`Not enough available accounts! You're trying to link ${selectedUnlinkedProfiles.length} profiles, but only ${availableAccountsCount} accounts are available.`);
      return;
    }

    // For manual mode, require account selection
    if (linkMode === 'manual' && !selectedAccount) {
      toast("Please select an account for manual linking");
      return;
    }
    
    setIsLinking(true);
    try {
      let linkPromises;
      
      if (linkMode === 'auto') {
        // Auto-assign: cycle through available accounts
        linkPromises = selectedUnlinkedProfiles.map((profileName, index) => {
          const account = availableAccounts[index % availableAccounts.length];
          return attachBulkProfile(profileName, account.id);
        });
      } else {
        // Manual: use selected account for all profiles
        linkPromises = selectedUnlinkedProfiles.map(profileName => 
          attachBulkProfile(profileName, selectedAccount!)
        );
      }
      
      await Promise.all(linkPromises);
      
      qc.invalidateQueries({ queryKey: ["profiles"] });
      qc.invalidateQueries({ queryKey: ["accounts"] });
      setSelectedProfiles(new Set());
      setErrorMessage(null); // Clear any error message on success
      toast(`Successfully linked ${selectedUnlinkedProfiles.length} profiles!`);
    } catch (error) {
      toast(`Error linking profiles: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsLinking(false);
    }
  };

  const unlinkSelectedProfiles = async () => {
    if (selectedProfiles.size === 0) return;
    
    // Filter to only linked profiles
    const selectedLinkedProfiles = Array.from(selectedProfiles).filter(name => linkedProfiles.has(name));
    
    if (selectedLinkedProfiles.length === 0) {
      toast("No linked profiles selected for unlinking");
      return;
    }
    
    if (!confirm(`Are you sure you want to unlink ${selectedLinkedProfiles.length} profiles? This will remove their connections to bulkcreate profiles and accounts.`)) {
      return;
    }
    
    setIsLinking(true);
    try {
      // Find accounts that have the selected bulkcreate profile names
      const accountsToUnlink = accounts
        .filter(account => account.bulk_profile_name && selectedLinkedProfiles.includes(account.bulk_profile_name));
      
      if (accountsToUnlink.length === 0) {
        toast("No linked accounts found to unlink");
        return;
      }
      
      // Update accounts directly to remove bulk_profile_name
      const unlinkPromises = accountsToUnlink.map(account => {
        // Call the backend to unlink the account
        return fetch(`http://127.0.0.1:8000/accounts/${account.id}`, {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('jwt')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            bulk_profile_name: null,
            health: 'unknown'
          })
        });
      });
      
      await Promise.all(unlinkPromises);
      
      qc.invalidateQueries({ queryKey: ["profiles"] });
      qc.invalidateQueries({ queryKey: ["accounts"] });
      setSelectedProfiles(new Set());
      toast(`Successfully unlinked ${accountsToUnlink.length} profiles!`);
    } catch (error) {
      toast(`Error unlinking profiles: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsLinking(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
      <button
            onClick={handleSelectAll}
            className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            {selectedProfiles.size === unlinkedProfiles.length ? 'Deselect All' : 'Select All Unlinked'}
          </button>
          <button
            onClick={handleSelectAllLinked}
            className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            {selectedProfiles.size === linkedProfilesList.length ? 'Deselect All' : 'Select All Linked'}
          </button>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {selectedProfiles.size} selected
          </span>
        </div>
        
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          {/* Link Mode Selection */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Link Mode:</label>
            <div className="flex rounded-md border border-gray-300 dark:border-gray-600">
              <button
                onClick={() => setLinkMode('auto')}
                className={`px-3 py-1 text-xs ${
                  linkMode === 'auto' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                Auto
              </button>
              <button
                onClick={() => setLinkMode('manual')}
                className={`px-3 py-1 text-xs ${
                  linkMode === 'manual' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                Manual
              </button>
        </div>
          </div>

          {/* Account Status Indicator */}
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${availableAccountsCount > 0 ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {availableAccountsCount} available accounts
            </span>
          </div>

          {/* Manual Account Selection (only show in manual mode) */}
          {linkMode === 'manual' && (
            <select
              value={selectedAccount || ""}
              onChange={(e) => setSelectedAccount(Number(e.target.value))}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">Choose account...</option>
              {availableAccounts.map((account) => (
                <option key={account.id} value={account.id}>
                  @{account.handle}
                </option>
              ))}
            </select>
          )}
          
          <button
            onClick={linkSelectedProfiles}
            disabled={selectedProfiles.size === 0 || isLinking || (linkMode === 'manual' && !selectedAccount)}
            className={`rounded-md px-3 py-2 text-sm text-white disabled:opacity-50 ${
              errorMessage && linkMode === 'auto' && availableAccountsCount < selectedProfiles.size
                ? 'bg-red-600 hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600'
                : 'bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600'
            }`}
          >
            {isLinking ? 'Linking...' : `Link ${selectedProfiles.size} Profiles`}
      </button>

          <button
            onClick={unlinkSelectedProfiles}
            disabled={selectedProfiles.size === 0 || isLinking}
            className="rounded-md bg-red-600 px-3 py-2 text-sm text-white hover:bg-red-700 disabled:opacity-50 dark:bg-red-500 dark:hover:bg-red-600"
          >
            {isLinking ? 'Unlinking...' : `Unlink ${selectedProfiles.size} Profiles`}
          </button>
        </div>
      </div>

      {/* Error Message Card */}
      {errorMessage && (
        <div className="fixed top-4 right-4 z-50 max-w-md">
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 shadow-lg dark:border-red-800 dark:bg-red-900/20">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Insufficient Accounts
                </h3>
                <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                  {errorMessage}
                </p>
                <div className="mt-3">
                  <button
                    onClick={() => setErrorMessage(null)}
                    className="text-sm font-medium text-red-800 hover:text-red-900 dark:text-red-200 dark:hover:text-red-100"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div>
        <input
          type="text"
          placeholder="Search profiles..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-400"
        />
          </div>

      {/* Stats */}
      <div className="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400">
        <span>Total: {profileEntries.length}</span>
        <span>Linked: {linkedCount}</span>
        <span>Available: {unlinkedProfiles.length}</span>
        <span className="flex items-center gap-1">
          <div className={`h-2 w-2 rounded-full ${availableAccountsCount > 0 ? 'bg-green-500' : 'bg-red-500'}`}></div>
          Accounts: {availableAccountsCount}
        </span>
      </div>

      {/* Profile List */}
      <div className="max-h-96 overflow-y-auto space-y-2">
        {filteredProfiles.map(([name, profile]) => {
          const isLinked = linkedProfiles.has(name);
          const isSelected = selectedProfiles.has(name);
          const enhanced = profile.enhancedMode;
          const linkedAccount = profileToAccountMap.get(name);
          
          return (
            <div
              key={name}
              className={`flex items-center gap-3 rounded-lg border p-3 ${
                isLinked 
                  ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-700' 
                  : isSelected 
                    ? 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-700' 
                    : 'bg-white border-gray-200 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:hover:bg-gray-700'
              }`}
            >
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => handleProfileSelect(name)}
                className="h-4 w-4 text-blue-600"
              />
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <code className="text-sm font-medium text-gray-900 dark:text-white">{name}</code>
                  <span className={`rounded px-2 py-0.5 text-xs ${
                    enhanced ? 'bg-purple-50 text-purple-700 dark:bg-purple-900/20 dark:text-purple-300' : 'bg-gray-50 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                  }`}>
                    {enhanced ? 'Enhanced' : 'Standard'}
                  </span>
                  {isLinked && (
                    <span className="rounded bg-green-50 px-2 py-0.5 text-xs text-green-700 dark:bg-green-900/20 dark:text-green-300">
                      Linked
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 truncate" title={profile.user_agent}>
                  {profile.user_agent || 'Unknown User Agent'}
                </div>
                {linkedAccount && (
                  <div className="mt-1 text-xs text-green-600 dark:text-green-400">
                    → Linked to @{linkedAccount.handle} (ID: {linkedAccount.id})
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


function AccountSidebarItem({ 
  account, 
  isSelected, 
  onSelect,
  onDelete
}: { 
  account: AccountRow; 
  isSelected: boolean; 
  onSelect: () => void;
  onDelete: () => void;
}) {
  const isUnlinked = !account.bulk_profile_name && !account.adspower_profile_id;
  const [loginState, setLoginState] = useState<string | null>(null);
  const [isCheckingLogin, setIsCheckingLogin] = useState(false);
  const [isWarmingUp, setIsWarmingUp] = useState(false);
  const [warmupProgress, setWarmupProgress] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete();
  };

  const handleCheckLogin = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isCheckingLogin) return;
    
    setIsCheckingLogin(true);
    setLoginState(null);
    
    try {
      const result = await getLoginState(account.id);
      setLoginState(result.state);
      toast(`Login state for @${account.handle}: ${result.state}`);
    } catch (error) {
      setLoginState('error');
      toast(`Error checking login state: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsCheckingLogin(false);
    }
  };

  const handleWarmup = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isWarmingUp) return;
    
    setIsWarmingUp(true);
    setWarmupProgress("Starting warmup...");
    
    try {
      const eventSource = startWarmupStream(account.id, "reels", 90, 3);
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'progress') {
            setWarmupProgress(`Warming up... ${data.message || 'In progress'}`);
          } else if (data.type === 'done') {
            setWarmupProgress(`Warmup completed: ${data.reason || 'Finished'}`);
            eventSource.close();
            setIsWarmingUp(false);
            toast(`Warmup completed for @${account.handle}`);
          } else if (data.type === 'error') {
            setWarmupProgress(`Error: ${data.message}`);
            eventSource.close();
            setIsWarmingUp(false);
            toast(`Warmup error for @${account.handle}: ${data.message}`);
          }
        } catch (err) {
          console.error('Error parsing warmup event:', err);
        }
      };
      
      eventSource.onerror = () => {
        setWarmupProgress("Connection error");
        eventSource.close();
        setIsWarmingUp(false);
        toast(`Warmup connection error for @${account.handle}`);
      };
      
    } catch (error) {
      setWarmupProgress("Failed to start");
      setIsWarmingUp(false);
      toast(`Error starting warmup: ${error instanceof Error ? error.message : String(error)}`);
    }
  };
  
  return (
    <div 
      className={`rounded-lg border p-3 transition-colors ${
        isSelected
          ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
          : isUnlinked
            ? "border-yellow-200 bg-yellow-50 dark:border-yellow-700 dark:bg-yellow-900/20 hover:bg-yellow-100 dark:hover:bg-yellow-900/30"
            : "border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
      }`}
    >
      <div className="flex items-center justify-between">
        <div 
          className="flex-1 min-w-0 cursor-pointer"
          onClick={onSelect}
        >
          <div className="flex items-center gap-2 mb-1">
            <div className="font-medium text-gray-900 dark:text-white truncate">
              @{account.handle}
            </div>
            {isUnlinked && (
              <span className="rounded bg-yellow-100 px-2 py-0.5 text-xs text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200">
                Unlinked
              </span>
            )}
            {isSelected && (
              <span className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-800 dark:bg-blue-800 dark:text-blue-200">
                Selected
              </span>
            )}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            ID: {account.id}
            {(account.bulk_profile_name || account.adspower_profile_id) && ` • Profile: ${account.bulk_profile_name || account.adspower_profile_id}`}
          </div>
          {account.bulk_profile_name && (
            <div className="flex items-center gap-1 mt-1">
              <span className="rounded bg-blue-50 px-1 py-0.5 text-xs text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">Bulk</span>
              <span className="text-xs">{account.bulk_profile_name}</span>
            </div>
          )}
          {account.adspower_profile_id && (
            <div className="flex items-center gap-1 mt-1">
              <span className="rounded bg-gray-50 px-1 py-0.5 text-xs text-gray-700 dark:bg-gray-700 dark:text-gray-300">AdsPower</span>
              <span className="text-xs">{account.adspower_profile_id}</span>
            </div>
          )}
        </div>
        
        {/* Action buttons for linked accounts */}
        {!isUnlinked && (
          <div className="flex flex-col gap-1 mt-2">
            {/* Login State Check */}
            <div className="flex items-center gap-2">
            <button 
                onClick={handleCheckLogin}
                disabled={isCheckingLogin}
                className="flex-1 rounded-md bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:bg-blue-400 dark:bg-blue-500 dark:hover:bg-blue-600 disabled:dark:bg-blue-700"
              >
                {isCheckingLogin ? "Checking..." : "Check Login"}
            </button>
              {loginState && (
                <span className={`text-xs px-1 py-0.5 rounded ${
                  loginState === 'logged_in' ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200' :
                  loginState === 'login' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200' :
                  loginState === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200' :
                  'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                }`}>
                  {loginState}
                </span>
              )}
            </div>
            
            {/* Warmup Button */}
            <div className="flex items-center gap-2">
            <button 
                onClick={handleWarmup}
                disabled={isWarmingUp}
                className="flex-1 rounded-md bg-green-600 px-2 py-1 text-xs text-white hover:bg-green-700 disabled:bg-green-400 dark:bg-green-500 dark:hover:bg-green-600 disabled:dark:bg-green-700"
              >
                {isWarmingUp ? "Warming..." : "Warmup"}
            </button>
              {warmupProgress && (
                <span className="text-xs text-gray-600 dark:text-gray-400 truncate max-w-32">
                  {warmupProgress}
                </span>
              )}
            </div>
          </div>
        )}
        
            <button 
          onClick={handleDelete}
          className="ml-2 rounded-md bg-red-600 px-2 py-1 text-xs text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600"
            >
          ×
            </button>
      </div>
    </div>
  );
}

function AccountDetails({ 
  account, 
  onClose 
}: { 
  account: AccountRow | undefined; 
  onClose: () => void; 
}) {
  if (!account) return null;

  const isUnlinked = !account.bulk_profile_name && !account.adspower_profile_id;

  return (
    <div className="space-y-6">
      {/* Account Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            @{account.handle}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Account ID: {account.id}
          </p>
        </div>
            <button 
          onClick={onClose}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            >
          Close
            </button>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className={`rounded-lg border p-4 ${
          isUnlinked 
            ? 'border-yellow-200 bg-yellow-50 dark:border-yellow-700 dark:bg-yellow-900/20' 
            : 'border-green-200 bg-green-50 dark:border-green-700 dark:bg-green-900/20'
        }`}>
          <div className="flex items-center gap-2">
            <div className={`h-3 w-3 rounded-full ${
              isUnlinked ? 'bg-yellow-500' : 'bg-green-500'
            }`}></div>
            <span className="font-medium text-gray-900 dark:text-white">
              {isUnlinked ? 'Unlinked' : 'Linked'}
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {isUnlinked 
              ? 'This account is not connected to any profile' 
              : 'This account is connected to a profile'
            }
          </p>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-blue-500"></div>
            <span className="font-medium text-gray-900 dark:text-white">
              Profile Type
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {account.bulk_profile_name ? 'Bulkcreate Profile' : 
             account.adspower_profile_id ? 'AdsPower Profile' : 
             'No Profile Connected'}
          </p>
        </div>
      </div>

      {/* Profile Information */}
      {(account.bulk_profile_name || account.adspower_profile_id) && (
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Profile Information
          </h3>
          <div className="space-y-3">
            {account.bulk_profile_name && (
              <div className="flex items-center gap-3">
                <span className="rounded bg-blue-50 px-2 py-1 text-xs text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">
                  Bulkcreate
                </span>
                <code className="text-sm">{account.bulk_profile_name}</code>
              </div>
            )}
            {account.adspower_profile_id && (
              <div className="flex items-center gap-3">
                <span className="rounded bg-gray-50 px-2 py-1 text-xs text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                  AdsPower
                </span>
                <code className="text-sm">{account.adspower_profile_id}</code>
              </div>
            )}
            {(account.bulk_profile_name || account.adspower_profile_id) && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                <strong>Profile:</strong> {account.bulk_profile_name || account.adspower_profile_id}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
          Actions
        </h3>
        <div className="flex flex-wrap gap-2">
          <button className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600">
            View Profile
          </button>
          <button className="rounded-md border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-white">
            Edit Account
          </button>
          {isUnlinked && (
            <button className="rounded-md bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600">
              Link Profile
            </button>
          )}
        </div>
      </div>

      {/* Account Stats */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
          Account Statistics
        </h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">Created:</span>
            <span className="ml-2 text-gray-900 dark:text-white">Unknown</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Last Activity:</span>
            <span className="ml-2 text-gray-900 dark:text-white">Unknown</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Status:</span>
            <span className="ml-2 text-gray-900 dark:text-white">
              {isUnlinked ? 'Inactive' : 'Active'}
            </span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Profile Status:</span>
            <span className="ml-2 text-gray-900 dark:text-white">
              {isUnlinked ? 'Not Connected' : 'Connected'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function AccountRowItem({ account, onError }: { account: AccountRow, onError?: (id: number, error: string) => void }) {
  const [open, setOpen] = useState(false);
  const [loginState, setLoginState] = useState<string | null>(null);
  const [isCheckingLogin, setIsCheckingLogin] = useState(false);
  const [isWarmingUp, setIsWarmingUp] = useState(false);
  const [warmupProgress, setWarmupProgress] = useState<string | null>(null);
  const [warmupTimeLeft, setWarmupTimeLeft] = useState<number | null>(null);
  
  const hasProfile = !!(account.bulk_profile_name || account.adspower_profile_id);
  const isUnlinked = !hasProfile;

  const handleCheckLogin = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isCheckingLogin) return;
    
    setIsCheckingLogin(true);
    setLoginState(null);
    
    try {
      const result = await getLoginState(account.id);
      setLoginState(result.state);
      toast(`Login state for @${account.handle}: ${result.state}`);
    } catch (error) {
      setLoginState('error');
      toast(`Error checking login state: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsCheckingLogin(false);
    }
  };

  const handleWarmup = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isWarmingUp) return;
    
    setIsWarmingUp(true);
    setWarmupProgress("Starting warmup...");
    setWarmupTimeLeft(90); // 90 seconds duration (60-90s range)
    
    // Start countdown timer
    const timer = setInterval(() => {
      setWarmupTimeLeft(prev => {
        if (prev === null || prev <= 1) {
          clearInterval(timer);
          return null;
        }
        return prev - 1;
      });
    }, 1000);
    
    try {
      const eventSource = startWarmupStream(account.id, "reels", 90, 3);
      
          eventSource.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data);
              if (data.type === 'start') {
                setWarmupProgress(`Starting warmup: ${data.content} mode`);
              } else if (data.type === 'phase_switch') {
                setWarmupProgress(`Switching to ${data.to} feed...`);
              } else if (data.type === 'next_reel') {
                setWarmupProgress(`Scrolling reels... ${data.count} movements`);
              } else if (data.type === 'like') {
                setWarmupProgress(`Liked ${data.liked} posts`);
              } else if (data.type === 'scroll') {
                setWarmupProgress(`Scrolling home feed... ${data.scrolled} scrolls`);
              } else if (data.type === 'pause') {
                setWarmupProgress(`Pausing... ${data.duration?.toFixed(1)}s`);
              } else if (data.type === 'debug') {
                setWarmupProgress(`Debug: ${data.message}`);
              } else if (data.type === 'done') {
                setWarmupProgress(`Warmup completed: ${data.reason} (${data.liked} likes, ${data.scrolled} scrolls)`);
                setWarmupTimeLeft(null);
                eventSource.close();
                setIsWarmingUp(false);
                clearInterval(timer);
                toast(`Warmup completed for @${account.handle}: ${data.liked} likes, ${data.scrolled} scrolls`);
              } else if (data.type === 'error') {
                setWarmupProgress(`Error: ${data.message}`);
                setWarmupTimeLeft(null);
                eventSource.close();
                setIsWarmingUp(false);
                clearInterval(timer);
                toast(`Warmup error for @${account.handle}: ${data.message}`);
              }
            } catch (err) {
              console.error('Error parsing warmup event:', err);
            }
          };
      
      eventSource.onerror = () => {
        setWarmupProgress("Connection error");
        setWarmupTimeLeft(null);
        eventSource.close();
        setIsWarmingUp(false);
        clearInterval(timer);
        toast(`Warmup connection error for @${account.handle}`);
      };
      
    } catch (error) {
      setWarmupProgress("Failed to start");
      setWarmupTimeLeft(null);
      setIsWarmingUp(false);
      clearInterval(timer);
      toast(`Error starting warmup: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  return (
    <div className="rounded-xl border bg-white dark:border-gray-700 dark:bg-gray-800">
      {/* Header */}
            <button
        className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700"
        onClick={() => setOpen((s) => !s)}
      >
        <div className="flex min-w-0 items-center gap-3">
          {account.bulk_profile_name ? (
            <div className="flex items-center gap-2">
              <span className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">Bulk</span>
              <code className="truncate text-xs text-gray-500">{account.bulk_profile_name}</code>
            </div>
          ) : account.adspower_profile_id ? (
            <div className="flex items-center gap-2">
              <span className="rounded bg-gray-50 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-700 dark:text-gray-300">AdsPower</span>
              <code className="truncate text-xs text-gray-500">{account.adspower_profile_id}</code>
            </div>
          ) : (
            <span className="text-xs text-gray-400 dark:text-gray-500">No Profile</span>
          )}
          <span className="truncate text-sm text-gray-900 dark:text-white">
            @{account.handle}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <HealthBadge value={account.health || "unknown"} />
          {hasProfile && open && <LoginBadge id={account.id} onError={onError} />}
          <span className="text-xs text-gray-400 dark:text-gray-500">id #{account.id}</span>
        </div>
      </button>

      {/* Expanded Content */}
      {open && (
        <div className="border-t px-4 py-3 dark:border-gray-700">
          <div className="space-y-3">
            {/* Account Info */}
            <div className="text-sm">
              <div className="font-medium text-gray-900 dark:text-white">@{account.handle}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                ID: {account.id}
                {hasProfile && ` • Profile: ${account.bulk_profile_name || account.adspower_profile_id}`}
              </div>
            </div>

            {/* Profile Status */}
            <div className="flex items-center gap-2">
              <div className={`h-2 w-2 rounded-full ${isUnlinked ? 'bg-yellow-400' : 'bg-green-400'}`}></div>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {isUnlinked ? 'Unlinked' : 'Linked'}
              </span>
            </div>

            {/* Actions */}
            {hasProfile && (
              <div className="space-y-3">
                    {/* Login State and Warmup Buttons */}
                    <div className="space-y-3">
                      {/* Login State Check */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={handleCheckLogin}
                          disabled={isCheckingLogin}
                          className="rounded-md bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 disabled:bg-blue-400 dark:bg-blue-500 dark:hover:bg-blue-600 disabled:dark:bg-blue-700"
                        >
                          {isCheckingLogin ? "Checking..." : "Check Login"}
                        </button>
                        {loginState && (
                          <span className={`text-xs px-2 py-1 rounded ${
                            loginState === 'logged_in' ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200' :
                            loginState === 'login' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200' :
                            loginState === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200' :
                            'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                          }`}>
                            {loginState}
                          </span>
                        )}
                      </div>
                      
                      {/* Warmup Button */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={handleWarmup}
                          disabled={isWarmingUp}
                          className="rounded-md bg-green-600 px-3 py-1 text-xs text-white hover:bg-green-700 disabled:bg-green-400 dark:bg-green-500 dark:hover:bg-green-600 disabled:dark:bg-green-700"
                        >
                          {isWarmingUp ? "Warming..." : "Warmup"}
                          {warmupTimeLeft !== null && (
                            <span className="ml-1 text-xs">({warmupTimeLeft}s)</span>
                          )}
                        </button>
                        {warmupProgress && (
                          <span className="text-xs text-gray-600 dark:text-gray-400 truncate max-w-32">
                            {warmupProgress}
                          </span>
                        )}
                      </div>
                    </div>
                
                {/* Unlink Profile Button */}
                <div className="flex gap-2">
                  <button
                    onClick={async () => {
                      if (confirm(`Are you sure you want to unlink this profile? This will remove the connection to the bulkcreate profile.`)) {
                        try {
                          const response = await fetch(`http://127.0.0.1:8000/accounts/${account.id}`, {
                            method: 'PATCH',
                            headers: {
                              'Authorization': `Bearer ${localStorage.getItem('jwt')}`,
                              'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                              bulk_profile_name: null,
                              health: 'unknown'
                            })
                          });
                          
                          if (response.ok) {
                            toast("Profile unlinked successfully!");
                            // Refresh the page or invalidate queries
                            window.location.reload();
                          } else {
                            toast(`Error unlinking profile: ${response.statusText}`);
                          }
                        } catch (error) {
                          toast(`Error unlinking profile: ${error instanceof Error ? error.message : String(error)}`);
                        }
                      }
                    }}
                    className="rounded-md bg-red-600 px-3 py-1 text-xs text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600"
                  >
                    Unlink Profile
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Comprehensive Orphaned Links Manager Component
function OrphanedLinksManager({ accounts }: { accounts: any[] }) {
  const [isCleaning, setIsCleaning] = useState(false);
  const [orphanedLinks, setOrphanedLinks] = useState<any[]>([]);
  const [selectedLinks, setSelectedLinks] = useState<Set<number>>(new Set());
  const [autoCleanupEnabled, setAutoCleanupEnabled] = useState(false);
  const [cleanupInterval, setCleanupInterval] = useState(5);
  const [showOrphanedSection, setShowOrphanedSection] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const qc = useQueryClient();

  // Auto populate orphaned links when accounts data is available
  React.useEffect(() => {
    try {
      if (accounts && accounts.length > 0) {
        const linkedAccounts = accounts.filter(account => account.bulk_profile_name);
        setOrphanedLinks(linkedAccounts);
        setError(null);
      }
    } catch (err) {
      console.error("Error populating orphaned links:", err);
      setError("Failed to load orphaned links data");
    }
  }, [accounts]);

  // Auto cleanup effect
  React.useEffect(() => {
    if (!autoCleanupEnabled) return;

    const interval = setInterval(async () => {
      try {
        const result = await cleanupOrphanedLinks();
        if (result.cleaned_count > 0) {
          toast(`Auto cleanup: cleaned ${result.cleaned_count} orphaned links`);
          qc.invalidateQueries({ queryKey: ["accounts"] });
                      qc.invalidateQueries({ queryKey: ["profiles"] });
                    }
      } catch (error) {
        console.error("Auto cleanup failed:", error);
      }
    }, cleanupInterval * 1000);

    return () => clearInterval(interval);
  }, [autoCleanupEnabled, cleanupInterval, qc]);

  const detectMutation = useMutation({
    mutationFn: detectOrphanedLinks,
    onSuccess: (data) => {
      setOrphanedLinks(data.orphaned_accounts || []);
      if (data.orphaned_count > 0) {
        toast(`Found ${data.orphaned_count} orphaned links`);
        setShowOrphanedSection(true);
      } else {
        toast("No orphaned links found");
        setShowOrphanedSection(false);
      }
    },
    onError: (error) => {
      toast(`Detection failed: ${error.message}`);
      // Show a fallback section with manual detection
      setShowOrphanedSection(true);
      setOrphanedLinks([]);
    }
  });

  const cleanupAllMutation = useMutation({
    mutationFn: cleanupOrphanedLinks,
    onSuccess: (data) => {
      toast(`Successfully cleaned ${data.cleaned_count} orphaned links`);
      setOrphanedLinks([]);
      setSelectedLinks(new Set());
      setShowOrphanedSection(false);
      qc.invalidateQueries({ queryKey: ["accounts"] });
      qc.invalidateQueries({ queryKey: ["profiles"] });
    },
    onError: (error) => {
      toast(`Error cleaning orphaned links: ${error.message}`);
    }
  });

  const cleanupSelectedMutation = useMutation({
    mutationFn: cleanupSelectedOrphanedLinks,
    onSuccess: (data) => {
      toast(`Successfully cleaned ${data.cleaned_count} selected orphaned links`);
      setOrphanedLinks(prev => prev.filter(link => !selectedLinks.has(link.id)));
      setSelectedLinks(new Set());
      qc.invalidateQueries({ queryKey: ["accounts"] });
      qc.invalidateQueries({ queryKey: ["profiles"] });
    },
    onError: (error) => {
      toast(`Error cleaning selected links: ${error.message}`);
    }
  });

  const handleDetect = async () => {
    // Refresh the orphaned links data
    if (accounts && accounts.length > 0) {
      const linkedAccounts = accounts.filter(account => account.bulk_profile_name);
      setOrphanedLinks(linkedAccounts);
      toast(`Refreshed: Found ${linkedAccounts.length} linked accounts`);
    } else {
      setOrphanedLinks([]);
      toast("No accounts data available");
    }
  };

  const handleCleanupAll = async () => {
    if (!confirm("Are you sure you want to clean up ALL orphaned links?")) {
      return;
    }
    setIsCleaning(true);
    try {
      await cleanupAllMutation.mutateAsync();
    } finally {
      setIsCleaning(false);
    }
  };

  const handleCleanupSelected = async () => {
    if (selectedLinks.size === 0) {
      toast("Please select orphaned links to clean up");
      return;
    }
    if (!confirm(`Are you sure you want to clean up ${selectedLinks.size} selected orphaned links?`)) {
      return;
    }
    setIsCleaning(true);
    try {
      await cleanupSelectedMutation.mutateAsync(Array.from(selectedLinks));
    } finally {
      setIsCleaning(false);
    }
  };

  const handleSelectAll = () => {
    if (selectedLinks.size === orphanedLinks.length) {
      setSelectedLinks(new Set());
    } else {
      setSelectedLinks(new Set(orphanedLinks.map(link => link.id)));
    }
  };

  const handleSelectLink = (linkId: number) => {
    const newSelected = new Set(selectedLinks);
    if (newSelected.has(linkId)) {
      newSelected.delete(linkId);
    } else {
      newSelected.add(linkId);
    }
    setSelectedLinks(newSelected);
  };

  const handleAutoCleanupToggle = async () => {
    const newEnabled = !autoCleanupEnabled;
    setAutoCleanupEnabled(newEnabled);
    try {
      await updateAutoCleanupSettings(newEnabled, cleanupInterval);
      toast(`Auto cleanup ${newEnabled ? 'enabled' : 'disabled'}`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      toast(`Failed to update auto cleanup settings: ${errorMessage}`);
      setAutoCleanupEnabled(!newEnabled); // Revert on error
    }
  };

  // Show error if there's one
  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4 dark:bg-red-900/20">
        <div className="text-sm text-red-800 dark:text-red-200">
          Error: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Control Panel */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleDetect}
          disabled={detectMutation.isPending}
          className="rounded-md bg-yellow-600 px-3 py-2 text-sm text-white hover:bg-yellow-700 disabled:opacity-50 dark:bg-yellow-500 dark:hover:bg-yellow-600"
        >
          {detectMutation.isPending ? "Detecting..." : "Detect Orphaned Links"}
            </button>

        <button
          onClick={handleCleanupAll}
          disabled={isCleaning || orphanedLinks.length === 0}
          className="rounded-md bg-red-600 px-3 py-2 text-sm text-white hover:bg-red-700 disabled:opacity-50 dark:bg-red-500 dark:hover:bg-red-600"
        >
          {isCleaning ? "Cleaning..." : `Clean All (${orphanedLinks.length})`}
        </button>

        {/* Auto Cleanup Toggle */}
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoCleanupEnabled}
              onChange={handleAutoCleanupToggle}
              className="rounded"
            />
            Auto Cleanup
          </label>
          {autoCleanupEnabled && (
            <select
              value={cleanupInterval}
              onChange={(e) => setCleanupInterval(Number(e.target.value))}
              className="rounded border px-2 py-1 text-sm"
            >
              <option value={5}>5s</option>
              <option value={10}>10s</option>
              <option value={30}>30s</option>
              <option value={60}>1m</option>
            </select>
          )}
          </div>
        </div>

      {/* Orphaned Links Section */}
      {showOrphanedSection && orphanedLinks.length > 0 && (
        <Card>
          <CardHeader 
            title="Orphaned Links Found" 
            subtitle={`${orphanedLinks.length} accounts linked to non-existent bulkcreate profiles`}
          />
          <CardBody>
            <div className="space-y-4">
              {/* Selection Controls */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSelectAll}
                    className="rounded-md bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
                  >
                    {selectedLinks.size === orphanedLinks.length ? "Deselect All" : "Select All"}
                  </button>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedLinks.size} of {orphanedLinks.length} selected
                  </span>
                </div>
                <button
                  onClick={handleCleanupSelected}
                  disabled={isCleaning || selectedLinks.size === 0}
                  className="rounded-md bg-orange-600 px-3 py-1 text-xs text-white hover:bg-orange-700 disabled:opacity-50 dark:bg-orange-500 dark:hover:bg-orange-600"
                >
                  Clean Selected ({selectedLinks.size})
                </button>
              </div>

              {/* Orphaned Links List */}
              <div className="max-h-64 overflow-y-auto space-y-2">
                {orphanedLinks.map((link) => (
                  <div
                    key={link.id}
                    className={`flex items-center gap-3 rounded-lg border p-3 ${
                      selectedLinks.has(link.id)
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                        : "border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedLinks.has(link.id)}
                      onChange={() => handleSelectLink(link.id)}
                      className="rounded"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 dark:text-white">
                        @{link.handle}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        ID: {link.id} • Profile: {link.bulk_profile_name}
                      </div>
                    </div>
                    <div className="text-xs text-yellow-600 dark:text-yellow-400">
                      Linked (Check if orphaned)
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}