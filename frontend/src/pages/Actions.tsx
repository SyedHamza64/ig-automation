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
  type ActionRequest 
} from "../api/actions";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { Table, TBody, TD } from "../components/ui/Table";
import { toast } from "../components/ui/Toast";

type ActionType = "follow" | "unfollow" | "like-recent";

export default function ActionsPage() {
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [actionType, setActionType] = useState<ActionType>("follow");
  const [usernames, setUsernames] = useState<string>("");
  const [count, setCount] = useState<number>(2);
  
  const queryClient = useQueryClient();

  // Load accounts
  const { data: accounts = [], isLoading: accountsLoading } = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
  });

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
    if (!selectedAccount || !selectedAccount.profile_id) {
      toast("Please select an account with a linked profile", "error");
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
      profile_id: selectedAccount.profile_id,
      usernames: usernameList,
    };

    if (actionType === "like-recent") {
      payload.count = count;
      likeRecentMutation.mutate(payload);
    } else if (actionType === "follow") {
      followMutation.mutate(payload);
    } else if (actionType === "unfollow") {
      unfollowMutation.mutate(payload);
    }
  };

  const isLoading = followMutation.isPending || unfollowMutation.isPending || likeRecentMutation.isPending;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Actions</h1>

      {/* Action Form */}
      <Card>
        <CardHeader title="Run Action" />
        <CardBody className="space-y-4">
          {/* Account Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Account
            </label>
            {accountsLoading ? (
              <div className="text-sm text-gray-500">Loading accounts...</div>
            ) : (
              <select
                value={selectedAccountId || ""}
                onChange={(e) => setSelectedAccountId(Number(e.target.value))}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Select an account...</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    @{account.handle} {account.profile_id ? `(Profile: ${account.profile_id})` : "(No Profile)"}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Action Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
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
                    className="mr-2"
                  />
                  <span className="text-sm capitalize">{type.replace("-", " ")}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Usernames Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Usernames
            </label>
            <input
              type="text"
              value={usernames}
              onChange={(e) => setUsernames(e.target.value)}
              placeholder="Enter usernames separated by commas (e.g., instagram, natgeo, nike)"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Separate multiple usernames with commas
            </p>
          </div>

          {/* Count Input (for like-recent) */}
          {actionType === "like-recent" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Posts to Like
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                className="w-32 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          )}

          {/* Submit Button */}
          <div>
            <button
              onClick={handleSubmit}
              disabled={isLoading || !selectedAccount || !selectedAccount.profile_id}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                isLoading || !selectedAccount || !selectedAccount.profile_id
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                  : "bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              }`}
            >
              {isLoading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Running...
                </span>
              ) : (
                `Run ${actionType.replace("-", " ")}`
              )}
            </button>
          </div>
        </CardBody>
      </Card>

      {/* Recent Actions Table */}
      <Card>
        <CardHeader title="Recent Actions" />
        <CardBody>
          {logsLoading ? (
            <div className="text-sm text-gray-500">Loading recent actions...</div>
          ) : recentLogs.length === 0 ? (
            <div className="text-sm text-gray-500">No recent actions found</div>
          ) : (
            <Table>
              <TBody>
                {recentLogs.map((log: any) => (
                  <tr key={log.id} className="border-t">
                    <TD className="text-xs text-gray-500">
                      {log.id}
                    </TD>
                    <TD className="text-sm">
                      @{log.account_handle || "Unknown"}
                    </TD>
                    <TD>
                      <span className={`rounded px-2 py-0.5 text-xs ${
                        log.action === 'like' ? 'bg-red-100 text-red-700' :
                        log.action === 'follow' ? 'bg-blue-100 text-blue-700' :
                        log.action === 'unfollow' ? 'bg-gray-100 text-gray-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {log.action}
                      </span>
                    </TD>
                    <TD>
                      <span className={`rounded px-2 py-0.5 text-xs ${
                        log.status === 'success' ? 'bg-green-100 text-green-700' :
                        log.status === 'error' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {log.status}
                      </span>
                    </TD>
                    <TD className="text-sm">
                      {log.result ? (
                        <div className="max-w-xs truncate">
                          {Array.isArray(log.result) ? 
                            log.result.map((r: any, i: number) => (
                              <div key={i} className="text-xs">
                                {r.username}: {r.status}
                              </div>
                            )) :
                            JSON.stringify(log.result)
                          }
                        </div>
                      ) : "—"}
                    </TD>
                    <TD className="text-xs text-gray-500">
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
