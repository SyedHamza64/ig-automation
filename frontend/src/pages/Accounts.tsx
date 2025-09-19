import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listAccounts, createAccount, deleteAccount, type Account } from "../api/accounts";
import { openProfile, getLoginState, type LoginState } from "../api/profiles";
import { Table, THead, TBody, TH, TD } from "../components/ui/Table";
import { Card, CardBody, CardHeader } from "../components/ui/Card";

export default function AccountsPage() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["accounts"], queryFn: listAccounts });

  const [username, setUsername] = useState("");
  const [profileId, setProfileId] = useState<string>("");

  const mCreate = useMutation({
    mutationFn: () => createAccount({ username, profile_id: profileId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["accounts"] });
      setUsername(""); setProfileId("");
    },
  });

  const mDelete = useMutation({
    mutationFn: (id: number) => deleteAccount(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["accounts"] }),
  });

  const mOpen = useMutation({
    mutationFn: (pid: number | string) => openProfile(pid),
    onSuccess: () => {
      // let the badge pick it up on next poll automatically
    },
  });

  const rows: Account[] = useMemo(() => q.data || [], [q.data]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Accounts" subtitle="Manage Instagram accounts and open AdsPower profiles" />
        <CardBody>
          {/* Add form */}
          <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Field label="Username" value={username} onChange={setUsername} placeholder="natgeo" />
            <Field label="Profile ID" value={profileId} onChange={setProfileId} placeholder="1" />
            <div className="flex items-end">
              <Btn
                text={mCreate.isPending ? "Adding..." : "Add Account"}
                onClick={() => username && mCreate.mutate()}
                disabled={!username}
              />
            </div>
          </div>

          {/* Table */}
          <Table>
            <THead>
              <tr>
                <TH>ID</TH>
                <TH>Username</TH>
                <TH>Profile</TH>
                <TH>Login State</TH>
                <TH>Actions</TH>
              </tr>
            </THead>
            <TBody>
              {rows.length === 0 ? (
                <tr><TD colSpan={5}>No accounts yet.</TD></tr>
              ) : (
                rows.map((a) => (
                  <tr key={a.id}>
                    <TD>#{a.id}</TD>
                    <TD>{a.username}</TD>
                    <TD>{a.profile_id ?? "-"}</TD>
                    <TD>
                      {a.profile_id ? (
                        <LoginStateBadge profileId={String(a.profile_id)} />
                      ) : (
                        <span className="text-xs text-gray-400">no profile</span>
                      )}
                    </TD>
                    <TD className="space-x-2">
                      {a.profile_id ? (
                        <Btn
                          text={mOpen.isPending ? "Opening..." : "Open Profile"}
                          onClick={() => mOpen.mutate(String(a.profile_id))}
                        />
                      ) : null}
                      <Btn kind="danger" text={mDelete.isPending ? "Deleting..." : "Delete"} onClick={() => mDelete.mutate(a.id)} />
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

function Field({
  label, value, onChange, placeholder,
}: { label: string; value: string; onChange: (v: string) => void; placeholder?: string; }) {
  return (
    <label className="block">
      <div className="mb-1 text-sm text-gray-600">{label}</div>
      <input
        className="w-full rounded-md border px-3 py-2"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}

function Btn({
  text, onClick, kind = "default", disabled,
}: { text: string; onClick: () => void; kind?: "default" | "danger"; disabled?: boolean; }) {
  const cls =
    kind === "danger"
      ? "border-red-300 text-red-700 hover:bg-red-50"
      : "border-gray-300 text-gray-700 hover:bg-gray-50";
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`rounded-md border px-3 py-2 text-sm disabled:opacity-50 ${cls}`}
    >
      {text}
    </button>
  );
}

/** Polls /engine/login-state?profile_id=… every 15s */
function LoginStateBadge({ profileId }: { profileId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["login-state", profileId],
    queryFn: () => getLoginState(profileId),
    refetchInterval: 15000,
  });

  if (isLoading) return <span className="text-xs text-gray-400">checking…</span>;
  if (isError) return <span className="text-xs text-red-600">error</span>;

  const state = (data?.state ?? "unknown") as LoginState;
  const styles: Record<LoginState, string> = {
    logged_in: "bg-green-50 text-green-700",
    login: "bg-yellow-50 text-yellow-700",
    error: "bg-red-50 text-red-700",
    unknown: "bg-gray-50 text-gray-500",
  };

  return (
    <span className={`rounded px-2 py-0.5 text-xs ${styles[state]}`}>
      {state}
    </span>
  );
}
