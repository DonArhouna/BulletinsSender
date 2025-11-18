import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { User, Mail, Calendar, LogOut } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

interface UserDetailsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ApiUser {
  id: number;
  email: string;
  username?: string | null;
  full_name?: string | null;
  company?: string | null;
  is_superuser?: boolean;
  is_active?: boolean;
  created_at?: string;
}

const UserDetailsDialog = ({ open, onOpenChange }: UserDetailsDialogProps) => {
  const navigate = useNavigate();
  const [user, setUser] = useState<ApiUser | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMe = async () => {
      if (!open) return;
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem("token");
        if (!token) throw new Error("Non authentifié");
        const res = await fetch("http://localhost:8000/api/v1/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          throw new Error("Échec du chargement des informations utilisateur");
        }
        const data: ApiUser = await res.json();
        setUser(data);
      } catch (e: any) {
        setError(e.message || "Erreur inattendue");
      } finally {
        setLoading(false);
      }
    };
    fetchMe();
  }, [open]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    onOpenChange(false);
    navigate("/login");
  };

  const displayName = user?.full_name || user?.username || user?.email || "Utilisateur";
  const role = user?.is_superuser ? "Super Admin" : "Client";
  const createdDate = user?.created_at ? new Date(user.created_at).toLocaleDateString() : undefined;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Détails de l'utilisateur</DialogTitle>
          <DialogDescription>
            Consultez vos informations personnelles et gérez votre compte.
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

          {!loading && !error && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <User className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Nom</p>
                  <p className="font-medium">{displayName}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <Mail className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Email</p>
                  <p className="font-medium">{user?.email}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <User className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Rôle</p>
                  <p className="font-medium">{role}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <Calendar className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Membre depuis</p>
                  <p className="font-medium">{createdDate || "-"}</p>
                </div>
              </div>
            </div>
          )}

          <Button
            onClick={handleLogout}
            variant="destructive"
            className="w-full mt-4"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Se déconnecter
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default UserDetailsDialog;
