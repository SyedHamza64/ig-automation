import { useQuery } from "@tanstack/react-query";
import { getHealth } from "../api/health";
import { listAccounts } from "../api/accounts";
import { listRecentLogs, type ActionLog } from "../api/logs";
import { listProfiles } from "../api/profiles";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { Table, THead, TBody, TH, TD } from "../components/ui/Table";

export default function Overview() {
  const qHealth = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: false,
  });
  const qAccounts = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
  });
  const qLogs = useQuery({
    queryKey: ["recent-logs"],
    queryFn: () => listRecentLogs(20),
    refetchInterval: 15000,
  });
  const qProfiles = useQuery({
    queryKey: ["profiles"],
    queryFn: listProfiles,
    refetchInterval: 30000,
  });

  const accounts = qAccounts.data || [];
  const logs = qLogs.data || [];
  const profiles = qProfiles.data || [];

  const successRecent = logs.filter((l) => l.status === "success").length;
  
  // Profile statistics
  const bulkcreateProfiles = profiles.filter((p) => !!p.bulk_profile_name).length;
  const adspowerProfiles = profiles.filter((p) => !!p.adspower_profile_id).length;
  const linkedProfiles = profiles.filter((p) => !!p.account_id).length;

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-6">
        <StatCard
          title="Backend Health"
          value={healthText(qHealth)}
          subtitle="/health/live → /health/db"
        />
        <StatCard
          title="Accounts"
          value={accounts.length}
          subtitle="Total connected"
        />
        <StatCard
          title="Bulkcreate Profiles"
          value={bulkcreateProfiles}
          subtitle="Enhanced automation"
        />
        <StatCard
          title="AdsPower Profiles"
          value={adspowerProfiles}
          subtitle="Legacy profiles"
        />
        <StatCard
          title="Linked Profiles"
          value={linkedProfiles}
          subtitle="Connected to accounts"
        />
        <StatCard
          title="Success (recent)"
          value={successRecent}
          subtitle="Last 20 logs"
        />
      </div>

      {/* Logs table */}
      <Card>
        <CardHeader title="Recent Activity" subtitle="Latest 20 action logs" />
        <CardBody>
          <Table>
            <THead>
              <tr>
                <TH>Time</TH>
                <TH>Account</TH>
                <TH>Action</TH>
                <TH>Status</TH>
                <TH>Result</TH>
              </tr>
            </THead>
            <TBody>
              {logs.length === 0 ? (
                <tr>
                  <TD colSpan={5}>No logs yet.</TD>
                </tr>
              ) : (
                logs.map((l: ActionLog) => (
                  <tr key={l.id}>
                    <TD>{fmt(l.created_at)}</TD>
                    <TD>#{l.account_id}</TD>
                    <TD>{labelAction(l.action)}</TD>
                    <TD>
                      <span
                        className={`rounded px-2 py-0.5 text-xs ${
                          l.status === "success"
                            ? "bg-green-50 text-green-700"
                            : "bg-red-50 text-red-700"
                        }`}
                      >
                        {l.status}
                      </span>
                    </TD>
                    <TD>
                      <code className="block max-w-[28rem] truncate text-xs text-gray-500">
                        {formatResult(l)}
                      </code>
                    </TD>
                  </tr>
                ))
              )}
            </TBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
}

function StatCard({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
}) {
  return (
    <Card>
      <CardBody className="space-y-1">
        <div className="text-sm text-gray-500 dark:text-gray-400">{subtitle}</div>
        <div className="text-lg font-semibold text-gray-900 dark:text-white">{title}</div>
        <div className="text-3xl font-bold text-gray-900 dark:text-white">{value}</div>
      </CardBody>
    </Card>
  );
}

function healthText(q: any) {
  if (q.isLoading) return "…";
  if (q.isError) return "down";
  return typeof q.data === "string" ? q.data : "ok";
}

function fmt(iso?: string) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function labelAction(a?: string) {
  if (!a) return "";
  const norm = a.toLowerCase();
  if (norm === "like" || norm === "like_recent") return "Like Recent";
  if (norm === "unfollow") return "Unfollow";
  if (norm === "follow") return "Follow";
  return a;
}

function formatResult(l: ActionLog): string {
    if (l.error_message) return `Error: ${l.error_message}`;
    if (!l.result) return "";
  
    try {
      // unwrap nested structure: result.results[0].results
      if (
        l.result.results &&
        Array.isArray(l.result.results) &&
        l.result.results[0]?.results
      ) {
        const inner = l.result.results[0];
        const username = inner.username || "unknown";
        const statuses = inner.results
          .map((r: any) => r.status)
          .filter(Boolean)
          .join(", ");
        return `${username}: ${statuses}`;
      }
  
      // fallback if result is already flat
      if (Array.isArray(l.result.results)) {
        const statuses = l.result.results
          .map((r: any) => r.status)
          .filter(Boolean)
          .join(", ");
        return statuses;
      }
  
      return JSON.stringify(l.result);
    } catch {
      return String(l.result);
    }
  }
  
