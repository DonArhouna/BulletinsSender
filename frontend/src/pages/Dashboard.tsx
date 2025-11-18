import { useEffect, useState } from "react";
import { StatCard } from "@/components/StatCard";
import { MonthlyChart } from "@/components/MonthlyChart";
import { RecentActivity } from "@/components/RecentActivity";
import { Mail, Users, CheckCircle, TrendingUp } from "lucide-react";

type Stats = {
  total: number;
  sent: number;
  failed: number;
  pending: number;
  last7Days: { day: string; count: number }[];
};

type UserStats = {
  total_users: number;
  active_employees: number;
};

const Dashboard = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [userStats, setUserStats] = useState<UserStats | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    // Fetch email stats (normaliser la forme de la réponse)
      fetch("http://localhost:8000/api/v1/email-stats", {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(async (res) => {
          const txt = await res.text();
          let json: unknown = null;
          try {
            json = txt ? JSON.parse(txt) : null;
          } catch (e) {
            console.error("Erreur parsing email-stats:", e, txt);
          }
          const parsed = json as unknown as { detail?: string; message?: string } | null;
          if (!res.ok) {
            console.error("Réponse email-stats:", txt);
            throw new Error((parsed && (parsed.detail || parsed.message)) || txt || `HTTP ${res.status}`);
          }
          return json;
        })
      .then((data) => {
        // Le backend retourne normalement un objet; si il est enveloppé, on essaie de normaliser
        const dataObj = data as Record<string, unknown>;
        const normalized = dataObj && (dataObj.data || dataObj.result || dataObj.results) ? (dataObj.data || dataObj.result || dataObj.results) : dataObj;
        setStats(normalized as Stats);
      })
      .catch((err) => {
        console.error("Erreur lors du fetch des stats emails:", err);
      });

    // Fetch user stats (superadmin endpoint)
    fetch("http://localhost:8000/api/v1/users-stats", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        const txt = await res.text();
  let json: unknown = null;
        try {
          json = txt ? JSON.parse(txt) : null;
        } catch (e) {
          console.error("Erreur parsing users-stats:", e, txt);
        }
  const parsed = json as unknown as { detail?: string; message?: string } | null;
  if (!res.ok) throw new Error((parsed && (parsed.detail || parsed.message)) || txt || `HTTP ${res.status}`);
        return json;
      })
      .then((data) => setUserStats(data as UserStats))
      .catch((error) => {
        console.error("Erreur lors du chargement des stats utilisateurs:", error);
      });
  }, []);

  return (
    <div className="p-6">
      <div className="space-y-6">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-foreground mb-2">
            Bienvenue sur votre tableau de bord
          </h2>
          <p className="text-muted-foreground">
            Vue d'ensemble de vos envois de bulletins de salaire
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
          <StatCard
            title="Total Envoyés"
            value={stats ? String(stats.sent) : "—"}
            change=""
            changeType="positive"
            icon={Mail}
          />
          <StatCard
            title="Taux de Succès"
            value={stats ? `${stats.sent && stats.total ? ((stats.sent / Math.max(stats.total, 1)) * 100).toFixed(1) : 0}%` : "—"}
            change=""
            changeType="positive"
            icon={CheckCircle}
          />
          <StatCard
            title="Total Utilisateurs"
            value={userStats ? String(userStats.total_users) : "—"}
            change=""
            changeType="positive"
            icon={Users}
          />
          <StatCard
            title="Employés Actifs"
            value={userStats ? String(userStats.active_employees) : "—"}
            change=""
            changeType="positive"
            icon={TrendingUp}
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <MonthlyChart />
          <RecentActivity />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
