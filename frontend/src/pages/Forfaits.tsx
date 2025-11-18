import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Package, Plus, Edit, Trash2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/hooks/use-toast";

interface SubscriptionPlan { id: number; name: string; duration_months: number; }
interface PricingPlan { id: number; subscription_plan_id: number; price_per_bulletin: number; currency: string; is_active: boolean; }

const Forfaits = () => {
  const [open, setOpen] = useState(false);
  const [subs, setSubs] = useState<SubscriptionPlan[]>([]);
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [form, setForm] = useState({ subscription_plan_id: 0, price_per_bulletin: 0.0, currency: "EUR" });
  const [editOpen, setEditOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<PricingPlan | null>(null);
  const [editForm, setEditForm] = useState({ subscription_plan_id: 0, price_per_bulletin: 0.0, currency: "EUR" });

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const [resSubs, resPlans] = await Promise.all([
        fetch("http://localhost:8000/api/v1/subscriptions/plans", { headers: { Authorization: `Bearer ${token}` } }),
        fetch("http://localhost:8000/api/v1/pricing/plans", { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      if (resSubs.ok) setSubs(await resSubs.json());
      if (resPlans.ok) setPlans(await resPlans.json());
    } catch {
      toast({ title: "Erreur", description: "Chargement des forfaits/abonnements échoué", variant: "destructive" });
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8000/api/v1/pricing/plans", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        toast({ title: "Succès", description: "Forfait créé" });
        setOpen(false);
        setForm({ subscription_plan_id: 0, price_per_bulletin: 0.0, currency: "EUR" });
        fetchData();
      } else {
        const err = await res.json();
        toast({ title: "Erreur", description: err.detail || "Échec de création", variant: "destructive" });
      }
    } catch {
      toast({ title: "Erreur", description: "Erreur réseau", variant: "destructive" });
    }
  };

  const handleDeletePlan = async (id: number) => {
    if (!confirm("Désactiver ce forfait ?")) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:8000/api/v1/pricing/plans/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        toast({ title: "Désactivé", description: "Forfait désactivé" });
        fetchData();
      } else {
        let errText = "Impossible de désactiver le forfait";
        try { const err = await res.json(); if (err?.detail) errText = err.detail; } catch (e) { console.warn("Failed to parse error body", e); }
        toast({ title: "Erreur", description: errText, variant: "destructive" });
      }
    } catch {
      toast({ title: "Erreur", description: "Erreur réseau", variant: "destructive" });
    }
  };

  const openEditDialog = (plan: PricingPlan) => {
    setEditingPlan(plan);
    setEditForm({ subscription_plan_id: plan.subscription_plan_id, price_per_bulletin: plan.price_per_bulletin, currency: plan.currency });
    setEditOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPlan) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:8000/api/v1/pricing/plans/${editingPlan.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(editForm),
      });
      if (res.ok) {
        toast({ title: "Modifié", description: "Forfait mis à jour" });
        setEditOpen(false);
        setEditingPlan(null);
        fetchData();
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
        <h1 className="text-3xl font-bold">Forfaits</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Nouveau
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Créer un nouveau forfait</DialogTitle>
              <DialogDescription>
                Ajoutez les informations du forfait
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="abonnement">Abonnement</Label>
                <Select value={String(form.subscription_plan_id)} onValueChange={(v) => setForm({ ...form, subscription_plan_id: Number(v) })}>
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
                <Label htmlFor="prix-bulletin">Tarif par bulletin</Label>
                <Input id="prix-bulletin" type="number" step="0.01" value={form.price_per_bulletin} onChange={(e) => setForm({ ...form, price_per_bulletin: Number(e.target.value) })} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="currency">Devise</Label>
                <Input id="currency" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
              </div>
              <Button type="submit" className="w-full">Créer le forfait</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Liste des forfaits
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Abonnement</TableHead>
                <TableHead>Tarif par bulletin</TableHead>
                <TableHead>Devise</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {plans.map((p) => (
                <TableRow key={p.id}>
                  <TableCell>{subs.find((s) => s.id === p.subscription_plan_id)?.name || p.subscription_plan_id}</TableCell>
                  <TableCell>{p.price_per_bulletin.toFixed(2)}</TableCell>
                  <TableCell>{p.currency}</TableCell>
                  <TableCell>{p.is_active ? "Actif" : "Inactif"}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => openEditDialog(p)} aria-label="Modifier">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleDeletePlan(p.id)} aria-label="Désactiver">
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
            <DialogTitle>Modifier le forfait</DialogTitle>
            <DialogDescription>Mettre à jour les informations du forfait</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit-abonnement">Abonnement</Label>
              <Select value={String(editForm.subscription_plan_id)} onValueChange={(v) => setEditForm({ ...editForm, subscription_plan_id: Number(v) })}>
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
              <Label htmlFor="edit-prix-bulletin">Tarif par bulletin</Label>
              <Input id="edit-prix-bulletin" type="number" step="0.01" value={editForm.price_per_bulletin} onChange={(e) => setEditForm({ ...editForm, price_per_bulletin: Number(e.target.value) })} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-currency">Devise</Label>
              <Input id="edit-currency" value={editForm.currency} onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })} />
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

export default Forfaits;
