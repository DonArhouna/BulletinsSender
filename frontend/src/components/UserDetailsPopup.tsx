import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { User, Mail, Calendar, CreditCard, Building } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { useEffect, useState } from "react";

interface UserDetailsPopupProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userId: number | null;
}

interface UserDetails {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  subscription_plan_id?: number;
  pricing_plan_id?: number;
  tenant_id?: number;
  company?: string;
}

interface SubscriptionPlan {
  id: number;
  name: string;
  duration_months: number;
}

interface PricingPlan {
  id: number;
  price_per_bulletin: number;
  currency: string;
  subscription_plan_id?: number;
}

const UserDetailsPopup = ({ open, onOpenChange, userId }: UserDetailsPopupProps) => {
  const [user, setUser] = useState<UserDetails | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionPlan | null>(null);
  const [pricing, setPricing] = useState<PricingPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUserDetails = async () => {
      if (!open || !userId) return;
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem("token");

        // Fetch user details
        const userRes = await fetch(`http://localhost:8000/api/v1/users/${userId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!userRes.ok) throw new Error("Échec du chargement des détails utilisateur");
        const userData: UserDetails = await userRes.json();
        setUser(userData);

        // Fetch subscription plan if exists
        if (userData.subscription_plan_id) {
          const subRes = await fetch(`http://localhost:8000/api/v1/subscriptions/plans/${userData.subscription_plan_id}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (subRes.ok) setSubscription(await subRes.json());
        }

        // Fetch pricing plan if exists
        if (userData.pricing_plan_id) {
          const pricingRes = await fetch(`http://localhost:8000/api/v1/pricing/plans/${userData.pricing_plan_id}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (pricingRes.ok) setPricing(await pricingRes.json());
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Erreur inattendue");
      } finally {
        setLoading(false);
      }
    };
    fetchUserDetails();
  }, [open, userId]);

  const displayName = user?.full_name || user?.email || "Utilisateur";
  const role = user?.is_superuser ? "Super Admin" : "Client";
  const createdDate = user?.created_at ? new Date(user.created_at).toLocaleDateString() : undefined;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Détails de l'utilisateur</DialogTitle>
          <DialogDescription>
            Informations complètes sur l'utilisateur sélectionné.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-6">
          <div className="flex justify-center">
            <Avatar className="h-20 w-20">
              <AvatarFallback className="bg-primary text-primary-foreground text-2xl">
                <User className="h-10 w-10" />
              </AvatarFallback>
            </Avatar>
          </div>

          {loading && (
            <p className="text-sm text-muted-foreground text-center">Chargement...</p>
          )}
          {error && (
            <p className="text-sm text-red-600 text-center">{error}</p>
          )}

          {!loading && !error && user && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <User className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Nom complet</p>
                  <p className="font-medium">{displayName}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <Mail className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Email</p>
                  <p className="font-medium">{user.email}</p>
                </div>
              </div>

              {user.company && (
                <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                  <Building className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Entreprise</p>
                    <p className="font-medium">{user.company}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <User className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Rôle</p>
                  <Badge variant={user.is_superuser ? "default" : "secondary"}>
                    {role}
                  </Badge>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <CreditCard className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Abonnement</p>
                  <p className="font-medium">
                    {subscription ? `${subscription.name} (${subscription.duration_months} mois)` : "Aucun abonnement"}
                  </p>
                  {pricing && (
                    <p className="text-xs text-muted-foreground">
                      Forfait: {pricing.price_per_bulletin.toFixed(2)} {pricing.currency} par bulletin
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Membre depuis</p>
                  <p className="font-medium">{createdDate || "-"}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <div className="h-5 w-5 flex items-center justify-center">
                  <div className={`h-3 w-3 rounded-full ${user.is_active ? 'bg-green-500' : 'bg-red-500'}`}></div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Statut</p>
                  <Badge variant={user.is_active ? "default" : "destructive"}>
                    {user.is_active ? "Actif" : "Inactif"}
                  </Badge>
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default UserDetailsPopup;