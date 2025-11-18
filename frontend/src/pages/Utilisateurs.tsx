import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Users, Plus, Edit, Trash2, Eye, Shield, ShieldOff } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import UserDetailsPopup from "@/components/UserDetailsPopup";

interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  tenant_id?: number;
  created_at: string;
}

interface Tenant {
  id: number;
  name: string;
  domain: string;
}

interface SubscriptionPlan { id: number; name: string; duration_months: number; }
interface PricingPlan { id: number; subscription_plan_id: number; price_per_bulletin: number; currency: string; }

const Utilisateurs = () => {
  const [open, setOpen] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [subs, setSubs] = useState<SubscriptionPlan[]>([]);
  const [pricings, setPricings] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
    tenant_id: "",
    is_superuser: false,
    subscription_plan_id: "",
    pricing_plan_id: "",
  });
  const [editOpen, setEditOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editForm, setEditForm] = useState({
    full_name: "",
    email: "",
    is_superuser: false,
    subscription_plan_id: "",
    pricing_plan_id: "",
  });
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch("http://localhost:8000/api/v1/users/", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger les utilisateurs",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchTenants = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch("http://localhost:8000/api/v1/tenants/", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setTenants(data);
      }
    } catch (error) {
      console.error("Erreur lors du chargement des tenants:", error);
    }
  };

  const fetchSubscriptionData = async () => {
    try {
      const token = localStorage.getItem("token");
      const [resSubs, resPricing] = await Promise.all([
        fetch("http://localhost:8000/api/v1/subscriptions/plans", { headers: { Authorization: `Bearer ${token}` } }),
        fetch("http://localhost:8000/api/v1/pricing/plans", { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      if (resSubs.ok) setSubs(await resSubs.json());
      if (resPricing.ok) setPricings(await resPricing.json());
    } catch (e) {
      console.error("Erreur chargement abonnements/forfaits", e);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchTenants();
    fetchSubscriptionData();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      const response = await fetch("http://localhost:8000/api/v1/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          full_name: formData.full_name,
          email: formData.email,
          password: formData.password,
          is_superuser: formData.is_superuser,
          subscription_plan_id: formData.subscription_plan_id ? Number(formData.subscription_plan_id) : null,
          pricing_plan_id: formData.pricing_plan_id ? Number(formData.pricing_plan_id) : null,
        }),
      });

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Utilisateur créé avec succès",
        });
        setOpen(false);
        setFormData({
          full_name: "",
          email: "",
          password: "",
          tenant_id: "",
          is_superuser: false,
          subscription_plan_id: "",
          pricing_plan_id: "",
        });
        fetchUsers();
      } else {
        const error = await response.json();
        toast({
          title: "Erreur",
          description: error.detail || "Erreur lors de la création",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Erreur réseau",
        variant: "destructive",
      });
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm("Êtes-vous sûr de vouloir supprimer cet utilisateur ?")) return;

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`http://localhost:8000/api/v1/users/${userId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Utilisateur supprimé",
        });
        fetchUsers();
      } else {
        toast({
          title: "Erreur",
          description: "Impossible de supprimer l'utilisateur",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Erreur réseau",
        variant: "destructive",
      });
    }
  };

  const handleBlockUser = async (userId: number, isCurrentlyActive: boolean) => {
    const action = isCurrentlyActive ? "bloquer" : "débloquer";
    if (!confirm(`Êtes-vous sûr de vouloir ${action} cet utilisateur ?`)) return;

    try {
      const token = localStorage.getItem("token");
      const endpoint = isCurrentlyActive ? "block" : "unblock";
      const response = await fetch(`http://localhost:8000/api/v1/users/${userId}/${endpoint}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        toast({
          title: "Succès",
          description: `Utilisateur ${isCurrentlyActive ? "bloqué" : "débloqué"}`,
        });
        fetchUsers();
      } else {
        const error = await response.json();
        toast({
          title: "Erreur",
          description: error.detail || `Impossible de ${action} l'utilisateur`,
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Erreur réseau",
        variant: "destructive",
      });
    }
  };

  const openEditDialog = (user: User) => {
    setEditingUser(user);
    setEditForm({
      full_name: user.full_name,
      email: user.email || "",
      is_superuser: user.is_superuser,
      subscription_plan_id: "",
      pricing_plan_id: "",
    });
    setEditOpen(true);
  };

  const openDetailsDialog = (userId: number) => {
    setSelectedUserId(userId);
    setDetailsOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    const body: Record<string, unknown> = {};
  if (editForm.full_name) body.full_name = editForm.full_name;
  if (editForm.email) body.email = editForm.email;
  body.is_superuser = editForm.is_superuser;
    if (editForm.subscription_plan_id) body.subscription_plan_id = Number(editForm.subscription_plan_id);
    if (editForm.pricing_plan_id) body.pricing_plan_id = Number(editForm.pricing_plan_id);

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:8000/api/v1/users/${editingUser.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        toast({ title: "Modifié", description: "Utilisateur mis à jour" });
        setEditOpen(false);
        setEditingUser(null);
        fetchUsers();
      } else {
        const err = await res.json();
        toast({ title: "Erreur", description: err.detail || "Échec de la mise à jour", variant: "destructive" });
      }
    } catch (e) {
      toast({ title: "Erreur", description: "Erreur réseau", variant: "destructive" });
    }
  };

  if (loading) {
    return <div className="p-6">Chargement...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Gestion des Utilisateurs</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Nouveau
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nouvel Utilisateur</DialogTitle>
              <DialogDescription>
                Créez un nouvel utilisateur en remplissant les informations ci-dessous.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateUser} className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="nom">Nom complet</Label>
                <Input
                  id="nom"
                  placeholder="Ex: Jean Dupont"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email-user">Email</Label>
                <Input
                  id="email-user"
                  type="email"
                  placeholder="jean.dupont@entreprise.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Mot de passe</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                />
              </div>
            <div className="space-y-2">
              <Label htmlFor="role">Rôle</Label>
              <Select
                value={formData.is_superuser ? "superuser" : "user"}
                onValueChange={(value) => setFormData({ ...formData, is_superuser: value === "superuser" })}
              >
                <SelectTrigger id="role">
                  <SelectValue placeholder="Sélectionner un rôle" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">Utilisateur</SelectItem>
                  <SelectItem value="superuser">Super Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="abonnement">Abonnement</Label>
              <Select value={formData.subscription_plan_id} onValueChange={(v) => setFormData({ ...formData, subscription_plan_id: v })}>
                <SelectTrigger id="abonnement">
                  <SelectValue placeholder="Sélectionner un abonnement" />
                </SelectTrigger>
                <SelectContent>
                  {subs.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>
                      {s.name} ({s.duration_months} mois)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="forfait">Forfait</Label>
              <Select value={formData.pricing_plan_id} onValueChange={(v) => setFormData({ ...formData, pricing_plan_id: v })}>
                <SelectTrigger id="forfait">
                  <SelectValue placeholder="Sélectionner un forfait" />
                </SelectTrigger>
                <SelectContent>
                  {pricings.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>
                      {subs.find((s) => s.id === p.subscription_plan_id)?.name || p.subscription_plan_id} — {p.price_per_bulletin.toFixed(2)} {p.currency}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
              <Button type="submit" className="w-full">Créer l'utilisateur</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Liste des utilisateurs ({users.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nom</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Rôle</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.full_name}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    <Badge variant={user.is_superuser ? "default" : "secondary"}>
                      {user.is_superuser ? "Super Admin" : "Utilisateur"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={user.is_active ? "default" : "destructive"}>
                      {user.is_active ? "Actif" : "Inactif"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => openDetailsDialog(user.id)}>
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => openEditDialog(user)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleBlockUser(user.id, user.is_active)}
                        disabled={user.is_superuser} // Ne pas permettre de bloquer les super admins
                      >
                        {user.is_active ? <Shield className="h-4 w-4" /> : <ShieldOff className="h-4 w-4" />}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteUser(user.id)}
                        disabled={user.is_superuser} // Ne pas permettre de supprimer les super admins
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Edit Dialog for utilisateur */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Modifier l'utilisateur</DialogTitle>
            <DialogDescription>Mettre à jour les informations de l'utilisateur</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditSubmit} className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-nom">Nom complet</Label>
              <Input id="edit-nom" value={editForm.full_name} onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-email">Email</Label>
              <Input id="edit-email" type="email" value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-role">Rôle</Label>
              <Select value={editForm.is_superuser ? "superuser" : "user"} onValueChange={(v) => setEditForm({ ...editForm, is_superuser: v === "superuser" })}>
                <SelectTrigger id="edit-role">
                  <SelectValue placeholder="Sélectionner un rôle" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">Utilisateur</SelectItem>
                  <SelectItem value="superuser">Super Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-abonnement">Abonnement</Label>
              <Select value={editForm.subscription_plan_id} onValueChange={(v) => setEditForm({ ...editForm, subscription_plan_id: v })}>
                <SelectTrigger id="edit-abonnement">
                  <SelectValue placeholder="Sélectionner un abonnement" />
                </SelectTrigger>
                <SelectContent>
                  {subs.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>
                      {s.name} ({s.duration_months} mois)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-forfait">Forfait</Label>
              <Select value={editForm.pricing_plan_id} onValueChange={(v) => setEditForm({ ...editForm, pricing_plan_id: v })}>
                <SelectTrigger id="edit-forfait">
                  <SelectValue placeholder="Sélectionner un forfait" />
                </SelectTrigger>
                <SelectContent>
                  {pricings.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>
                      {subs.find((s) => s.id === p.subscription_plan_id)?.name || p.subscription_plan_id} — {p.price_per_bulletin.toFixed(2)} {p.currency}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2 justify-end">
              <Button type="button" variant="ghost" onClick={() => { setEditOpen(false); setEditingUser(null); }}>Annuler</Button>
              <Button type="submit">Mettre à jour</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* User Details Popup */}
      <UserDetailsPopup
        open={detailsOpen}
        onOpenChange={setDetailsOpen}
        userId={selectedUserId}
      />
    </div>
  );
};

export default Utilisateurs;
