import React, { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listProfiles, openProfile, closeProfile, wsCheck, probeProfile, getLoginState, startWarmupStream, type ProfileRow } from "../api/profiles";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { Table, TBody, TH, TD } from "../components/ui/Table";

type Tab = "linked" | "unlinked" | "all";

// Simple toast helper (non-blocking)
function toast(msg: string) { 
  console.log("[toast]", msg); 
}

export default function ProfilesPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["profiles"],
    queryFn: listProfiles,
    refetchInterval: 20000, // auto-refresh list
  });

  const [tab, setTab] = useState<Tab>("linked");
  const [q, setQ] = useState("");

  const rows = data || [];
  const counts = useMemo(() => {
    const linked = rows.filter((r) => !!r.account_id).length;
    return { total: rows.length, linked, unlinked: rows.length - linked };
  }, [rows]);

  // Collect all errors from login state queries
  const [errors, setErrors] = useState<Array<{id: number, error: string, adspower_id: string, account_handle?: string}>>([]);

  const handleError = (id: number, error: string) => {
    console.log(`[DEBUG] Error detected for profile ${id}:`, error);
    const profile = rows.find(r => r.id === id);
    if (profile) {
      setErrors(prev => {
        const existing = prev.find(e => e.id === id);
        if (existing) {
          return prev.map(e => e.id === id ? { ...e, error } : e);
        } else {
          return [...prev, { 
            id, 
            error, 
            adspower_id: profile.adspower_profile_id,
            account_handle: profile.account_handle || undefined
          }];
        }
      });
    }
  };

  const filtered = useMemo(() => {
    let r = rows;
    if (tab === "linked") r = r.filter((x) => !!x.account_id);
    if (tab === "unlinked") r = r.filter((x) => !x.account_id);
    if (q.trim()) {
      const s = q.trim().toLowerCase();
      r = r.filter(
        (x) =>
          x.adspower_profile_id?.toLowerCase().includes(s) ||
          x.account_handle?.toLowerCase().includes(s)
      );
    }
    return r;
  }, [rows, tab, q]);

  return (
    <div className="space-y-6">
      {/* Top summary + controls */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <Stat title="Total" value={counts.total} />
        <Stat title="Linked" value={counts.linked} />
        <Stat title="Unlinked" value={counts.unlinked} />
        <div className="flex items-end justify-end">
          <button
            disabled
            title="AdsPower free tier does not support API profile creation."
            className="rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-400"
          >
            Create Profile (stub)
          </button>
        </div>
      </div>

      {/* Error Section */}
      {errors.length > 0 && (
        <Card>
          <CardHeader title="Errors" subtitle={`${errors.length} profile(s) with errors`} />
          <CardBody>
            <div className="space-y-2">
              {errors.map((err) => (
                <div key={err.id} className="flex items-center justify-between rounded-md bg-red-50 p-3">
                  <div className="flex items-center gap-3">
                    <code className="text-xs text-red-600">{err.adspower_id}</code>
                    {err.account_handle && (
                      <span className="text-sm text-red-700">@{err.account_handle}</span>
                    )}
                    <span className="text-sm text-red-600">{err.error}</span>
                  </div>
                  <button
                    onClick={() => setErrors(prev => prev.filter(e => e.id !== err.id))}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Tabs + Search */}
      <Card>
        <CardHeader title="Profiles" subtitle="Linked / Unlinked / All" />
        <CardBody>
          <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="inline-flex overflow-hidden rounded-md border">
              <TabBtn active={tab === "linked"} onClick={() => setTab("linked")}>
                Linked
              </TabBtn>
              <TabBtn active={tab === "unlinked"} onClick={() => setTab("unlinked")}>
                Unlinked
              </TabBtn>
              <TabBtn active={tab === "all"} onClick={() => setTab("all")}>
                All
              </TabBtn>
            </div>
            <input
              className="w-full rounded-md border px-3 py-2 sm:w-64"
              placeholder="Search by AdsPower ID or account…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>

          {/* List */}
          {isLoading ? (
            <div className="py-8 text-sm text-gray-500">Loading…</div>
          ) : isError ? (
            <div className="py-8 text-sm text-red-600">Failed to load profiles.</div>
          ) : filtered.length === 0 ? (
            <div className="py-8 text-sm text-gray-500">No profiles.</div>
          ) : (
            <div className="space-y-2">
              {filtered.map((p) => (
                <ProfileRowItem key={p.id} row={p} onError={handleError} />
              ))}
            </div>
          )}
        </CardBody>
      </Card>
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
      className={`px-3 py-1.5 text-sm ${
        active ? "bg-gray-100 font-medium" : "bg-white hover:bg-gray-50"
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
        <div className="text-sm text-gray-500">{title}</div>
        <div className="text-2xl font-semibold">{value}</div>
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
    refetchInterval: 15000,
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

function ProfileRowItem({ row, onError }: { row: ProfileRow, onError?: (id: number, error: string) => void }) {
  const [open, setOpen] = useState(false);
  const [warming, setWarming] = useState(false);
  const [warmSecs, setWarmSecs] = useState<number>(0);
  const [warmTotal, setWarmTotal] = useState<number | null>(null);
  const qc = useQueryClient();
  
  const mOpen = useMutation({
    mutationFn: () => openProfile(row.id),
    onSuccess: () => { toast("Opened."); qc.invalidateQueries({ queryKey: ["profiles"] }); }
  });
  const mClose = useMutation({
    mutationFn: () => closeProfile(row.id),
    onSuccess: () => { toast("Closed."); qc.invalidateQueries({ queryKey: ["profiles"] }); }
  });
  const mProbe = useMutation({
    mutationFn: () => probeProfile(row.id),
    onSuccess: () => { toast("Probed & refreshed WS."); qc.invalidateQueries({ queryKey: ["profiles"] }); }
  });
  const mWs = useMutation({
    mutationFn: () => wsCheck(row.id),
    onSuccess: (res) => toast(res?.ok ? `WS OK (${res.host}:${res.port})` : `WS FAIL: ${res?.error ?? "unknown"}`)
  });

  return (
    <div className="rounded-xl border bg-white">
      {/* Header */}
      <button
        className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-gray-50"
        onClick={() => setOpen((s) => !s)}
      >
        <div className="flex min-w-0 items-center gap-3">
          <code className="truncate text-xs text-gray-500">{row.adspower_profile_id}</code>
          <span className="truncate text-sm">
            {row.account_handle ?? <span className="text-gray-400">—</span>}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <HealthBadge value={row.health} />
          <LoginBadge id={row.id} onError={onError} />
          <span className="text-xs text-gray-400">id #{row.id}</span>
        </div>
      </button>

      {/* Body (collapsible) */}
      {open && (
        <div className="px-4 pb-4">
          <div className="rounded-lg border bg-gray-50 p-3">
            <Table>
              <TBody>
                <tr>
                  <TH>Account</TH>
                  <TD>{row.account_handle ?? "—"} {row.account_id ? `(id #${row.account_id})` : ""}</TD>
                </tr>
                <tr>
                  <TH>AdsPower ID</TH>
                  <TD>
                    <code className="text-xs">{row.adspower_profile_id}</code>
                  </TD>
                </tr>
                <tr>
                  <TH>WS (last)</TH>
                  <TD>
                    {row.last_ws_puppeteer ? (
                      <code className="break-all text-xs">{row.last_ws_puppeteer}</code>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </TD>
                </tr>
              </TBody>
            </Table>
          </div>

          {/* Action buttons */}
          <div className="mt-3 flex flex-wrap gap-2">
            <button 
              onClick={() => mOpen.mutate()}  
              disabled={mOpen.isPending}  
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              {mOpen.isPending ? "Opening…" : "Open"}
            </button>
            <button 
              onClick={() => mClose.mutate()} 
              disabled={mClose.isPending} 
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              {mClose.isPending ? "Closing…" : "Close"}
            </button>
            <button 
              onClick={() => mWs.mutate()}    
              disabled={mWs.isPending}    
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              {mWs.isPending ? "WS…" : "WS Check"}
            </button>
            <button 
              onClick={() => mProbe.mutate()} 
              disabled={mProbe.isPending} 
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              {mProbe.isPending ? "Probing…" : "Probe"}
            </button>
            <button
              onClick={() => {
                if (warming) return;
                setWarming(true);
                setWarmSecs(0);
                setWarmTotal(null);
                const es = startWarmupStream(row.id, "reels", 0, -1);
                const startedAt = Date.now();
                const t = window.setInterval(() => setWarmSecs(Math.floor((Date.now()-startedAt)/1000)), 1000);
                es.onmessage = (e) => {
                  try {
                    const data = JSON.parse(e.data);
                    if (data?.type === "start") {
                      // duration_sec is in start event
                      if (typeof data.duration_sec === 'number') setWarmTotal(data.duration_sec);
                    }
                    if (data?.type === "done") {
                      es.close();
                      window.clearInterval(t);
                      setWarming(false);
                      qc.invalidateQueries({ queryKey: ["profiles"] });
                    }
                  } catch {}
                };
                es.onerror = () => {
                  es.close();
                  window.clearInterval(t);
                  setWarming(false);
                };
              }}
              disabled={warming}
              className={`rounded-md border px-3 py-1.5 text-sm disabled:opacity-50 ${warming ? "border-gray-300" : "border-gray-300 hover:bg-gray-50"}`}
            >
              {warming ? `Warming… ${warmSecs}${warmTotal?`/${warmTotal}`:""}s` : "Warmup"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
