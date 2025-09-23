import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { 
  listAccounts, 
  getAccountStats, 
  getRecentActions, 
  getAccountLimits,
  getLoginState,
  wsCheckProfile,
  type AccountRow,
  type LoginState
} from "../api/accounts";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { Table, TBody, TD } from "../components/ui/Table";

// Simple toast helper
function toast(msg: string) { 
  console.log("[toast]", msg); 
}

export default function AccountsPage() {
  console.log("[AccountsPage] Component rendering");
  
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);

  // Load accounts list
  const { data: accounts = [], isLoading: accountsLoading, error: accountsError } = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
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
    <div className="flex h-full">
      {/* Left sidebar - Account list */}
      <div className="w-80 border-r bg-gray-50 p-4">
        <h2 className="mb-4 text-lg font-semibold">Accounts ({accounts.length})</h2>
        {accounts.length === 0 ? (
          <div className="text-sm text-gray-500">No accounts found</div>
        ) : (
          <div className="space-y-2">
            {accounts.map((account) => (
              <button
                key={account.id}
                onClick={() => setSelectedAccountId(account.id)}
                className={`w-full rounded-lg border p-3 text-left transition-colors ${
                  selectedAccountId === account.id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 bg-white hover:bg-gray-50"
                }`}
              >
                <div className="font-medium">@{account.handle}</div>
                <div className="text-xs text-gray-500">
                  ID: {account.id}
                  {account.profile_id && ` • Profile: ${account.profile_id}`}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Right pane - Account details */}
      <div className="flex-1 p-6">
        {selectedAccount ? (
          <AccountDetails account={selectedAccount} />
        ) : (
          <div className="flex h-full items-center justify-center text-gray-500">
            Select an account to view details
          </div>
        )}
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

  // Login state (only if profile_id exists)
  const { data: loginState } = useQuery({
    queryKey: ["login-state", account.profile_id],
    queryFn: () => getLoginState(account.profile_id!),
    refetchInterval: 15000,
    enabled: !!account.profile_id,
  });

  // WS check (only if profile_id exists)
  const { data: wsCheck } = useQuery({
    queryKey: ["ws-check", account.profile_id],
    queryFn: () => wsCheckProfile(account.profile_id!),
    enabled: !!account.profile_id,
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
            {account.profile_id && ` • Profile: ${account.profile_id}`}
            {account.adspower_profile_id && ` • AdsPower: ${account.adspower_profile_id}`}
          </div>
        </div>
        <div className="flex gap-2">
          {account.profile_id && (
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