import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CreditCard, Plus, Edit, Trash2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";

interface SubscriptionPlan {
  id: number;
  name: string;
  duration_months: number;
  is_active: boolean;
}

const Abonnements = () => {
  const [open, setOpen] = useState(false);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [form, setForm] = useState({ name: "", duration_months: 1 });
  const [editOpen, setEditOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<SubscriptionPlan | null>(null);
  const [editForm, setEditForm] = useState({ name: "", duration_months: 1 });

  const fetchPlans = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8000/api/v1/subscriptions/plans", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPlans(data);
      }
    } catch {
      toast({ title: "Erreur", description: "Impossible de charger les abonnements", variant: "destructive" });
    }
  };

  useEffect(() => { fetchPlans(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8000/api/v1/subscriptions/plans", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        toast({ title: "Succès", description: "Abonnement créé" });
        setOpen(false);
        setForm({ name: "", duration_months: 1 });
        fetchPlans();
      } else {
        const err = await res.json();
        toast({ title: "Erreur", description: err.detail || "Échec de création", variant: "destructive" });
      }
    } catch {
      toast({ title: "Erreur", description: "Erreur réseau", variant: "destructive" });
    }
  };
  const openEditDialog = (plan: SubscriptionPlan) => {
    setEditingPlan(plan);
    setEditForm({ name: plan.name, duration_months: plan.duration_months });
    setEditOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPlan) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:8000/api/v1/subscriptions/plans/${editingPlan.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(editForm),
      });
      if (res.ok) {
        toast({ title: "Modifié", description: "Abonnement mis à jour" });
        setEditOpen(false);
        setEditingPlan(null);
        fetchPlans();
      } else {
        const err = await res.json();
        toast({ title: "Erreur", description: err.detail || "Échec de la mise à jour", variant: "destructive" });
      }
    } catch {
      toast({ title: "Erreur", description: "Erreur réseau", variant: "destructive" });
    }
  };

  const handleDeleteSubscription = async (id: number) => {
    if (!confirm("Désactiver cet abonnement ?")) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:8000/api/v1/subscriptions/plans/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        toast({ title: "Désactivé", description: "Abonnement désactivé" });
        fetchPlans();
      } else {
        let errText = "Impossible de désactiver l'abonnement";
   try { const err = await res.json(); if (err?.detail) errText = err.detail; } catch (e) { console.warn("Failed to parse error body", e); }
        toast({ title: "Erreur", description: errText, variant: "destructive" });
      }
    } catch {
      toast({ title: "Erreur", description: "Erreur réseau", variant: "destructive" });
    }
  };

  const handleEditSubscription = async (plan: SubscriptionPlan) => {
    const newName = prompt("Nom de l'abonnement:", plan.name);
    if (newName === null) return;
    const newDur = prompt("Durée (mois):", String(plan.duration_months));
    if (newDur === null) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:8000/api/v1/subscriptions/plans/${plan.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ name: newName, duration_months: Number(newDur) }),
      });
      if (res.ok) {
        toast({ title: "Modifié", description: "Abonnement mis à jour" });
        fetchPlans();
      } else {
        const err = await res.json();
        toast({ title: "Erreur", description: err.detail || "Échec de la mise à jour", variant: "destructive" });
      }
    } catch {
      toast({ title: "Erreur", description: "Erreur réseau", variant: "destructive" });
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Gestion des Abonnements</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Nouveau
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nouvel Abonnement</DialogTitle>
              <DialogDescription>
                Créez un nouvel abonnement en remplissant les informations ci-dessous.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="nom">Nom de l'abonnement</Label>
                <Input id="nom" placeholder="Ex: Basic, Semestriel, Annuel" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="duree">Durée (mois)</Label>
                <Input id="duree" type="number" min={1} value={form.duration_months} onChange={(e) => setForm({ ...form, duration_months: Number(e.target.value) })} required />
              </div>
              <Button type="submit" className="w-full">Créer l'abonnement</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Liste des abonnements ({plans.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nom</TableHead>
                <TableHead>Durée (mois)</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {plans.map((p) => (
                <TableRow key={p.id}>
                  <TableCell>{p.name}</TableCell>
                  <TableCell>{p.duration_months}</TableCell>
                  <TableCell>{p.is_active ? "Actif" : "Inactif"}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => openEditDialog(p)} aria-label="Modifier">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleDeleteSubscription(p.id)} aria-label="Désactiver">
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

      {/* Edit Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Modifier l'abonnement</DialogTitle>
            <DialogDescription>Mettre à jour les informations de l'abonnement</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit-nom">Nom de l'abonnement</Label>
              <Input id="edit-nom" placeholder="Ex: Basic, Semestriel, Annuel" value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-duree">Durée (mois)</Label>
              <Input id="edit-duree" type="number" min={1} value={editForm.duration_months} onChange={(e) => setEditForm({ ...editForm, duration_months: Number(e.target.value) })} required />
            </div>
            <div className="flex gap-2 justify-end">
              <Button type="button" variant="ghost" onClick={() => { setEditOpen(false); setEditingPlan(null); }}>Annuler</Button>
              <Button type="submit">Mettre à jour</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Abonnements;
