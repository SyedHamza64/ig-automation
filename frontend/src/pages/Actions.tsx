import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { 
  listAccounts
} from "../api/accounts";
import { 
  followAction, 
  unfollowAction, 
  likeRecentAction, 
  getRecentLogs,
  startMassFollowStream,
  type ActionRequest 
} from "../api/actions";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { Table, TBody, TD, THead, TH } from "../components/ui/Table";
import { toast } from "../components/ui/Toast";

type ActionType = "follow" | "unfollow" | "like-recent";

export default function ActionsPage() {
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [actionType, setActionType] = useState<ActionType>("follow");
  const [usernames, setUsernames] = useState<string>("");
  const [count, setCount] = useState<number>(2);
  const [followSection, setFollowSection] = useState<"followers" | "following">("followers");
  const [followLimit, setFollowLimit] = useState<number>(10);
  const [useMassFollow, setUseMassFollow] = useState<boolean>(true);
  const [streaming, setStreaming] = useState<boolean>(false);
  const [progress, setProgress] = useState<{acted:number; processed:number; total:number|null}>({acted:0, processed:0, total:0});
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  
  const queryClient = useQueryClient();

  // Load accounts
  const { data: accounts = [], isLoading: accountsLoading } = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
  });
  const accountById = new Map(accounts.map((a: any) => [a.id, a]));

  // Load recent logs
  const { data: recentLogs = [], isLoading: logsLoading } = useQuery({
    queryKey: ["recent-logs"],
    queryFn: () => getRecentLogs(50),
    refetchInterval: 20000,
  });

  // Auto-select first account
  const selectedAccount = accounts.find(acc => acc.id === selectedAccountId);
  if (accounts.length > 0 && !selectedAccountId) {
    setSelectedAccountId(accounts[0].id);
  }

  // Action mutations
  const followMutation = useMutation({
    mutationFn: followAction,
    onSuccess: (_, variables) => {
      toast(`Action queued: follow on ${variables.usernames.join(", ")}`, "success");
      queryClient.invalidateQueries({ queryKey: ["recent-logs"] });
    },
    onError: (error: any) => {
      toast(`Error: ${error?.response?.data?.detail || error?.message || "Unknown error"}`, "error");
    },
  });

  const unfollowMutation = useMutation({
    mutationFn: unfollowAction,
    onSuccess: (_, variables) => {
      toast(`Action queued: unfollow on ${variables.usernames.join(", ")}`, "success");
      queryClient.invalidateQueries({ queryKey: ["recent-logs"] });
    },
    onError: (error: any) => {
      toast(`Error: ${error?.response?.data?.detail || error?.message || "Unknown error"}`, "error");
    },
  });

  const likeRecentMutation = useMutation({
    mutationFn: likeRecentAction,
    onSuccess: (_, variables) => {
      toast(`Action queued: like-recent on ${variables.usernames.join(", ")} (${variables.count} posts)`, "success");
      queryClient.invalidateQueries({ queryKey: ["recent-logs"] });
    },
    onError: (error: any) => {
      toast(`Error: ${error?.response?.data?.detail || error?.message || "Unknown error"}`, "error");
    },
  });

  const handleSubmit = () => {
    if (!selectedAccount || (!selectedAccount.bulk_profile_name && !selectedAccount.adspower_profile_id)) {
      toast("Please select an account with a linked profile (bulkcreate or AdsPower)", "error");
      return;
    }

    const usernameList = usernames
      .split(",")
      .map(u => u.trim())
      .filter(u => u.length > 0);

    if (usernameList.length === 0) {
      toast("Please enter at least one username", "error");
      return;
    }

    const payload: ActionRequest = {
      account_id: selectedAccount.id,
      profile_id: selectedAccount.id, // Use account_id as profile_id since we merged the models
      usernames: usernameList,
    };

    if (actionType === "like-recent") {
      payload.count = count;
      likeRecentMutation.mutate(payload);
    } else if (actionType === "follow") {
      if (!useMassFollow) {
        // Fallback to existing queued follow API
        followMutation.mutate(payload);
      } else {
        // Use streaming mass-follow with section filter
        const username = usernameList[0];
        if (!username) {
          toast("Enter a single username for mass follow stream", "error");
          return;
        }
        setStreaming(true);
        setProgress({acted:0, processed:0, total:0});
        const es = startMassFollowStream({
          account_id: selectedAccount.id,
          profile_id: selectedAccount.id, // Use account_id as profile_id since we merged the models
          username,
          limit: followLimit,
          section: followSection,
        });
        es.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            if (data?.type === "start") {
              toast(`Started mass follow on @${username} (${followSection})`, "success");
            }
            if (data?.type === "progress") {
              setProgress({ acted: data.acted ?? 0, processed: data.processed ?? 0, total: data.total ?? null });
            }
            if (data?.type === "done") {
              toast(`Mass follow finished: ${data.reason}`, "success");
              es.close();
              setStreaming(false);
              queryClient.invalidateQueries({ queryKey: ["recent-logs"] });
            }
            if (data?.type === "error") {
              toast(`Error: ${data.message}`, "error");
            }
          } catch {}
        };
        es.onerror = () => {
          toast("Stream error", "error");
          es.close();
          setStreaming(false);
        };
      }
    } else if (actionType === "unfollow") {
      unfollowMutation.mutate(payload);
    }
  };

  const isLoading = followMutation.isPending || unfollowMutation.isPending || likeRecentMutation.isPending;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 space-y-6 p-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Actions</h1>

      {/* Action Form */}
      <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
        <CardHeader title="Run Action" />
        <CardBody className="space-y-4">
          {/* Account Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Select Account
            </label>
            {accountsLoading ? (
              <div className="text-sm text-gray-500 dark:text-gray-400">Loading accounts...</div>
            ) : (
              <select
                value={selectedAccountId || ""}
                onChange={(e) => setSelectedAccountId(Number(e.target.value))}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Select an account...</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    @{account.handle} {
                      account.bulk_profile_name 
                        ? `(Bulkcreate: ${account.bulk_profile_name})` 
                        : account.adspower_profile_id 
                          ? `(AdsPower: ${account.adspower_profile_id})` 
                          : "(No Profile)"
                    }
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Action Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Action Type
            </label>
            <div className="flex space-x-4">
              {(["follow", "unfollow", "like-recent"] as ActionType[]).map((type) => (
                <label key={type} className="flex items-center">
                  <input
                    type="radio"
                    name="actionType"
                    value={type}
                    checked={actionType === type}
                    onChange={(e) => setActionType(e.target.value as ActionType)}
                    className="mr-2 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm capitalize text-gray-900 dark:text-white">{type.replace("-", " ")}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Usernames Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Target Usernames
            </label>
            <input
              type="text"
              value={usernames}
              onChange={(e) => setUsernames(e.target.value)}
              placeholder="Enter usernames separated by commas (e.g., instagram, natgeo, nike)"
              className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 placeholder-gray-500 dark:placeholder-gray-400"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Separate multiple usernames with commas
            </p>
          </div>

          {/* Follow options (only for follow) */}
          {actionType === "follow" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Follow From</label>
                <select
                  value={followSection}
                  onChange={(e) => setFollowSection(e.target.value as any)}
                  className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="followers">Followers of username</option>
                  <option value="following">Following of username</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Follow Limit</label>
                <input
                  type="number"
                  min={1}
                  max={200}
                  value={followLimit}
                  onChange={(e) => setFollowLimit(Number(e.target.value))}
                  className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div className="md:col-span-2 flex items-center gap-3">
                <input id="toggleMassFollow" type="checkbox" checked={useMassFollow} onChange={(e)=>setUseMassFollow(e.target.checked)} className="text-blue-600 focus:ring-blue-500" />
                <label htmlFor="toggleMassFollow" className="text-sm text-gray-700 dark:text-gray-300">Use mass-follow stream (safer scrolling + delays)</label>
              </div>
            </div>
          )}

          {/* Count Input (for like-recent) */}
          {actionType === "like-recent" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Number of Posts to Like
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                className="w-32 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          )}

          {/* Submit Button */}
          <div>
            <button
              onClick={handleSubmit}
              disabled={isLoading || streaming || !selectedAccount || (!selectedAccount.bulk_profile_name && !selectedAccount.adspower_profile_id)}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                isLoading || streaming || !selectedAccount || (!selectedAccount.bulk_profile_name && !selectedAccount.adspower_profile_id)
                  ? "bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                  : "bg-blue-600 dark:bg-blue-700 text-white hover:bg-blue-700 dark:hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              }`}
            >
              {isLoading || streaming ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {`Running... ${progress.acted}/${followLimit}${progress.total ? ` (seen ${progress.processed}/${progress.total})` : ""}`}
                </span>
              ) : (
                `Run ${actionType.replace("-", " ")}`
              )}
            </button>
          </div>
        </CardBody>
      </Card>

      {/* Recent Actions Table */}
      <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
        <CardHeader title="Recent Actions" />
        <CardBody>
          {logsLoading ? (
            <div className="text-sm text-gray-500 dark:text-gray-400">Loading recent actions...</div>
          ) : recentLogs.length === 0 ? (
            <div className="text-sm text-gray-500 dark:text-gray-400">No recent actions found</div>
          ) : (
            <Table>
              <THead>
                <tr>
                  <TH className="w-16">ID</TH>
                  <TH>Account</TH>
                  <TH>Action</TH>
                  <TH>Status</TH>
                  <TH className="w-72">Results</TH>
                  <TH className="whitespace-nowrap">Time</TH>
                </tr>
              </THead>
              <TBody>
                {recentLogs.map((log: any) => (
                  <tr key={log.id} className="border-t border-gray-200 dark:border-gray-700">
                    <TD className="text-xs text-gray-500 dark:text-gray-400">
                      {log.id}
                    </TD>
                    <TD className="text-sm text-gray-900 dark:text-white">
                      @{accountById.get(log.account_id)?.handle || "Unknown"}
                    </TD>
                    <TD>
                      <span className={`rounded px-2 py-0.5 text-xs ${
                        (log.action === 'like' || log.action === 'like_recent') ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' :
                        log.action === 'follow' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' :
                        log.action === 'unfollow' ? 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' :
                        'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
                      }`}>
                        {String(log.action)}
                      </span>
                    </TD>
                    <TD>
                      <span className={`rounded px-2 py-0.5 text-xs ${
                        log.status === 'success' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
                        log.status === 'error' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' :
                        'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                      }`}>
                        {log.status}
                      </span>
                    </TD>
                    <TD className="text-sm text-gray-900 dark:text-white">
                      {log.result ? (
                        <div className="space-y-2">
                          {expandedRows.has(log.id) ? (
                            <div className="rounded border border-gray-200 bg-gray-50 p-2 text-xs text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300">
                              <pre className="whitespace-pre-wrap break-words overflow-x-auto">{JSON.stringify(log.result, null, 2)}</pre>
                            </div>
                          ) : (
                            <div className="max-w-xs truncate text-xs text-gray-600 dark:text-gray-400">
                              {(() => { const s = JSON.stringify(log.result); return s.slice(0,80) + (s.length>80 ? '…' : ''); })()}
                            </div>
                          )}
                          <button
                            onClick={() => {
                              setExpandedRows(prev => {
                                const next = new Set(prev);
                                if (next.has(log.id)) {
                                  next.delete(log.id);
                                } else {
                                  next.add(log.id);
                                }
                                return next;
                              });
                            }}
                            className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-0.5 text-xs text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                            aria-expanded={expandedRows.has(log.id)}
                          >
                            {expandedRows.has(log.id) ? 'Hide' : 'View'} results
                          </button>
                        </div>
                      ) : '—'}
                    </TD>
                    <TD className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(log.created_at).toLocaleString()}
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
