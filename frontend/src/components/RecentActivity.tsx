import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Clock, XCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Activity {
  id: string;
  fullName: string;
  email: string;
  sentCount: number;
  status: "success" | "pending" | "failed";
  date: string;
}

export const RecentActivity = () => {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchActivities = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const response = await fetch("http://localhost:8000/api/v1/email-recent-activity-users?limit=5", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setActivities(data);
      }
    } catch (error) {
      console.error("Error fetching recent activities:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, []);
  const getStatusIcon = (status: Activity["status"]) => {
    switch (status) {
      case "success":
        return <CheckCircle2 className="h-4 w-4 text-success" />;
      case "pending":
        return <Clock className="h-4 w-4 text-muted-foreground" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-destructive" />;
    }
  };

  const getStatusBadge = (status: Activity["status"]) => {
    const variants = {
      success: "bg-success/10 text-success border-success/20",
      pending: "bg-muted text-muted-foreground border-border",
      failed: "bg-destructive/10 text-destructive border-destructive/20",
    };

    const labels = {
      success: "Envoyé",
      pending: "En cours",
      failed: "Échec",
    };

    return (
      <Badge variant="outline" className={variants[status]}>
        {labels[status]}
      </Badge>
    );
  };

  return (
    <Card className="bg-gradient-card border-border/50 shadow-md">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-semibold">Activité Récente</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchActivities}
            disabled={isLoading}
            className="rounded-lg"
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? "animate-spin" : ""}`} />
            {isLoading ? "Chargement…" : "Rafraîchir"}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.length > 0 ? (
            activities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-center justify-between p-4 rounded-lg bg-background/50 border border-border/50 hover:bg-muted/30 transition-smooth"
              >
                <div className="flex items-start gap-4 flex-1">
                  {getStatusIcon(activity.status)}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground truncate">{activity.fullName}</p>
                    <p className="text-sm text-muted-foreground truncate">{activity.email}</p>
                    <p className="text-xs text-muted-foreground mt-1">{activity.sentCount} bulletins envoyés</p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2 ml-4">
                  {getStatusBadge(activity.status)}
                  <p className="text-xs text-muted-foreground whitespace-nowrap">{activity.date}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p>Aucune activité récente</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
