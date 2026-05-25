"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, Users, BarChart3, Database, Loader2, UserPlus, RefreshCw, AlertTriangle, CheckCircle2, LogOut } from "lucide-react";
import api from "@/lib/api-service";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

interface AdminStats {
  total_users?: number;
  total_freshers?: number;
  total_assessments?: number;
  total_submissions?: number;
  system_status?: string;
}

interface AdminUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  department?: string;
  is_active?: boolean;
}

const roles = [
  { value: "fresher", label: "Fresher" },
  { value: "manager", label: "Manager" },
  { value: "admin", label: "Admin" },
];

export default function AdminDashboardPage() {
  const router = useRouter();
  const { user, token, logout, isLoading: authLoading } = useAuth();

  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    email: "",
    password: "password123",
    first_name: "",
    last_name: "",
    role: "fresher",
    department: "Engineering",
  });
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);

  // Redirect non-admins
  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    const role = (user.role || "").toLowerCase();
    if (role !== "admin") {
      router.replace(role === "manager" ? "/dashboard/manager" : "/dashboard/fresher");
    }
  }, [authLoading, user, router]);

  const load = async () => {
    if (!token) { setError("Missing token"); setLoading(false); return; }
    setLoading(true);
    setError(null);
    try {
      const [s, u] = await Promise.all([
        api.admin.getStats(token),
        api.admin.getUsers(token),
      ]);
      if (s.error) setError(s.error);
      if (u.error) setError(u.error);
      if (s.data) setStats(s.data as AdminStats);
      if (u.data) {
        // Handle both array and wrapped response { users: [...] }
        const userList = Array.isArray(u.data) ? u.data : (u.data as any).users || [];
        setUsers(userList as AdminUser[]);
      }
    } catch (e) {
      setError("Failed to load admin data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (!authLoading) load(); }, [authLoading]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setStatusMsg(null);
    setError(null);
    const res = await api.admin.createUser(form, token);
    if (res.error) {
      setError(res.error);
    } else {
      setStatusMsg("User created");
      setForm({ ...form, email: "", first_name: "", last_name: "", role: "fresher" });
      load();
    }
  };

  const handleSeed = async () => {
    if (!token) return;
    setSeeding(true);
    setStatusMsg(null);
    setError(null);
    const res = await api.admin.seedData(token);
    if (res.error) setError(res.error);
    else setStatusMsg(res.data?.message || "Seed complete");
    setSeeding(false);
    load();
  };

  const statusColor = (role: string) => {
    const m: Record<string, string> = {
      admin: "bg-purple-100 text-purple-700",
      manager: "bg-blue-100 text-blue-700",
      fresher: "bg-green-100 text-green-700",
    };
    return m[role] || "bg-gray-100 text-gray-700";
  };

  return (
    <div className="dashboard-shell">
      <div className="blob-amber" aria-hidden />
      <header className="border-b bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 flex items-center justify-center text-white">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Admin Console</p>
            <h1 className="text-2xl font-bold text-gray-900">System Control</h1>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <button
              onClick={() => router.push("/dashboard/manager")}
              className="text-sm text-indigo-600 hover:underline"
            >
              Switch to Manager view
            </button>
            <button
              onClick={handleSeed}
              disabled={seeding}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium text-gray-700 hover:border-gray-400 disabled:opacity-60"
            >
              {seeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Seed test data
            </button>
            <button
              onClick={() => { logout(); router.push('/login'); }}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium text-red-600 hover:bg-red-50 hover:border-red-300 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}
        {statusMsg && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{statusMsg}</span>
          </div>
        )}

        {/* Stats */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Users", value: stats?.total_users ?? "-", icon: Users, color: "from-purple-500 to-indigo-600" },
            { label: "Freshers", value: stats?.total_freshers ?? "-", icon: BarChart3, color: "from-blue-500 to-cyan-500" },
            { label: "Assessments", value: stats?.total_assessments ?? "-", icon: ShieldCheck, color: "from-emerald-500 to-lime-500" },
            { label: "Submissions", value: stats?.total_submissions ?? "-", icon: Database, color: "from-amber-500 to-orange-500" },
          ].map((card) => {
            const Icon = card.icon;
            return (
              <div key={card.label} className="bg-white border rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">{card.label}</p>
                    <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                  </div>
                  <div className={cn("w-10 h-10 rounded-lg text-white flex items-center justify-center bg-gradient-to-br", card.color)}>
                    <Icon className="w-5 h-5" />
                  </div>
                </div>
              </div>
            );
          })}
        </section>

        {/* Create user */}
        <section className="bg-white border rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-gray-500">Provision</p>
              <h2 className="text-lg font-semibold text-gray-900">Create User</h2>
            </div>
            <UserPlus className="w-5 h-5 text-purple-600" />
          </div>
          <form onSubmit={handleCreateUser} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Email</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Password</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">First name</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2"
                value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Last name</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2"
                value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Role</label>
              <select
                className="mt-1 w-full rounded-lg border px-3 py-2"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
              >
                {roles.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Department</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2"
                value={form.department}
                onChange={(e) => setForm({ ...form, department: e.target.value })}
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <button
                type="submit"
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                <ShieldCheck className="w-4 h-4" />
                Create user
              </button>
            </div>
          </form>
        </section>

        {/* Users table */}
        <section className="bg-white border rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-gray-500">Directory</p>
              <h2 className="text-lg font-semibold text-gray-900">Users</h2>
            </div>
            {loading && <Loader2 className="w-5 h-5 animate-spin text-gray-500" />}
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Email</th>
                  <th className="py-2 pr-4">Role</th>
                  <th className="py-2 pr-4">Department</th>
                  <th className="py-2 pr-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {users.map((u) => (
                  <tr key={u.id} className="text-gray-800">
                    <td className="py-2 pr-4">{`${u.first_name || ""} ${u.last_name || ""}`.trim() || "-"}</td>
                    <td className="py-2 pr-4">{u.email}</td>
                    <td className="py-2 pr-4">
                      <span className={cn("px-2 py-1 rounded-full text-xs font-semibold capitalize", statusColor(u.role))}>
                        {u.role}
                      </span>
                    </td>
                    <td className="py-2 pr-4">{u.department || "-"}</td>
                    <td className="py-2 pr-4 text-sm text-gray-600">{u.is_active ? "Active" : "Inactive"}</td>
                  </tr>
                ))}
                {users.length === 0 && !loading && (
                  <tr>
                    <td className="py-4 text-gray-500" colSpan={5}>No users found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
