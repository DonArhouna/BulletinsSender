import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Calendar
} from "lucide-react";

interface Stats {
  total: number;
  sent: number;
  failed: number;
  pending: number;
}

export const MonthlyChart = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) return;

        const response = await fetch("http://localhost:8000/api/v1/email-stats", {
          headers: { Authorization: `Bearer ${token}` },
        });

        const txt = await response.text();
        let json: unknown = null;
        try {
          json = txt ? JSON.parse(txt) : null;
        } catch (e) {
          console.error("Erreur parsing monthly-chart stats:", e, txt);
        }

        if (!response.ok) {
          const parsed = json as { detail?: string; message?: string } | null;
          throw new Error((parsed && (parsed.detail || parsed.message)) || `HTTP ${response.status}`);
        }

  const parsed = json as unknown as { data?: Stats } | null;
  const normalized = parsed && parsed.data ? parsed.data : (json as unknown as Stats | null);
  if (normalized) setStats(normalized as Stats);
      } catch (error) {
        console.error("Error fetching stats:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  const successRate = stats ? ((stats.sent / Math.max(stats.total, 1)) * 100).toFixed(1) : "0";
  const failureRate = stats ? ((stats.failed / Math.max(stats.total, 1)) * 100).toFixed(1) : "0";
  const hasIssues = stats && stats.failed > 0;
  const isExcellent = stats && parseFloat(successRate) >= 95;

  return (
    <Card className="bg-gradient-card border-border/50 shadow-md">
      <CardHeader>
        <CardTitle className="text-xl font-semibold">Vue d'ensemble des Performances</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Indicateurs de performance */}
          <div className="grid grid-cols-2 gap-4">
            {/* Taux de réussite */}
            <div className="p-4 rounded-lg bg-success/10 border border-success/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">Taux de Réussite</span>
                <CheckCircle2 className="h-5 w-5 text-success" />
              </div>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-success">{successRate}%</span>
                {isExcellent && (
                  <TrendingUp className="h-5 w-5 text-success mb-1" />
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {stats?.sent || 0} envois réussis
              </p>
            </div>

            {/* Échecs */}
            <div className={`p-4 rounded-lg ${hasIssues ? 'bg-destructive/10 border border-destructive/20' : 'bg-muted/50 border border-border/50'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">Échecs</span>
                <AlertTriangle className={`h-5 w-5 ${hasIssues ? 'text-destructive' : 'text-muted-foreground'}`} />
              </div>
              <div className="flex items-end gap-2">
                <span className={`text-3xl font-bold ${hasIssues ? 'text-destructive' : 'text-muted-foreground'}`}>
                  {stats?.failed || 0}
                </span>
                {hasIssues && (
                  <TrendingDown className="h-5 w-5 text-destructive mb-1" />
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {failureRate}% du total
              </p>
            </div>
          </div>

          {/* Statistiques supplémentaires */}
          <div className="grid grid-cols-2 gap-4">
            {/* En attente */}
            <div className="p-3 rounded-lg bg-background/50 border border-border/50">
              <div className="flex items-center gap-2 mb-1">
                <Clock className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">En attente</span>
              </div>
              <span className="text-2xl font-bold">{stats?.pending || 0}</span>
            </div>

            {/* Total */}
            <div className="p-3 rounded-lg bg-background/50 border border-border/50">
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">Total envois</span>
              </div>
              <span className="text-2xl font-bold">{stats?.total || 0}</span>
            </div>
          </div>

          {/* Alertes et recommandations */}
          {hasIssues ? (
            <Alert className="bg-destructive/10 border-destructive/20">
              <AlertTriangle className="h-4 w-4 text-destructive" />
              <AlertDescription className="text-sm">
                <span className="font-semibold">Action requise :</span> {stats.failed} envoi(s) ont échoué.
                Vérifiez les adresses email et les configurations SMTP.
              </AlertDescription>
            </Alert>
          ) : (
            <Alert className="bg-success/10 border-success/20">
              <CheckCircle2 className="h-4 w-4 text-success" />
              <AlertDescription className="text-sm">
                <span className="font-semibold">Excellent !</span> Tous les envois fonctionnent correctement.
              </AlertDescription>
            </Alert>
          )}

          {/* Badge de statut */}
          <div className="flex items-center justify-between pt-2 border-t border-border/50">
            <span className="text-sm text-muted-foreground">Statut du système</span>
            <Badge variant={isExcellent ? "default" : hasIssues ? "destructive" : "secondary"}>
              {isExcellent ? "Excellent" : hasIssues ? "À surveiller" : "Normal"}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
