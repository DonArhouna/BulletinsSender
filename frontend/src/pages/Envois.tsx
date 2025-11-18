import { useEffect, useState } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Download, RefreshCw, Printer } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface SendItem {
  id: number;
  user_id: number;
  tenant_id?: number;
  nb_bulletins: number;
  price_per_bulletin: number;
  total_amount: number;
  invoice_number?: string;
  invoice_path?: string | null;
  created_at: string;
  status?: string;
  pricing_plan?: { currency?: string } | null;
}

interface UserMinimal { id: number; full_name?: string | null; email?: string }

interface CurrentUser {
  id: number;
  is_superuser: boolean;
}

const Envois = () => {
  const [sends, setSends] = useState<SendItem[]>([]);
  const [usersMap, setUsersMap] = useState<Record<number, string>>({});
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem("token");
        if (token) {
          // fetch current user info
          try {
            const resMe = await fetch("http://localhost:8000/api/v1/auth/me", { headers: { Authorization: `Bearer ${token}` } });
            if (resMe.ok) {
              const userData = await resMe.json();
              setCurrentUser({ id: userData.id, is_superuser: userData.is_superuser });
            }
          } catch (e) {
            console.error(e);
          }

          // fetch users only if superuser
          if (currentUser?.is_superuser) {
            try {
              const resUsers = await fetch("http://localhost:8000/api/v1/users/", { headers: { Authorization: `Bearer ${token}` } });
              if (resUsers.ok) {
                const data: UserMinimal[] = await resUsers.json();
                const map: Record<number, string> = {};
                data.forEach((u) => { map[u.id] = u.full_name || u.email || String(u.id); });
                setUsersMap(map);
              }
            } catch (e) {
              console.error(e);
            }
          }

          // fetch sends - API already filters by user for non-admins
          try {
            const res = await fetch("http://localhost:8000/api/v1/sends/?limit=200", { headers: { Authorization: `Bearer ${token}` } });
            if (res.ok) {
              const data = await res.json();
              setSends(data);
            }
          } catch (e) {
            toast({ title: "Erreur", description: "Impossible de charger les envois", variant: "destructive" });
          }
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [toast, currentUser?.is_superuser]);

  const handleDownload = async (s: SendItem) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/sends/${s.id}/invoice`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `facture_${s.invoice_number || s.id}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        toast({
          title: "Erreur",
          description: "Impossible de télécharger la facture",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Erreur réseau lors du téléchargement",
        variant: "destructive",
      });
    }
  };

  const handlePrint = async (s: SendItem) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/sends/${s.id}/invoice`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const printWindow = window.open(url, "_blank");
        if (printWindow) {
          printWindow.onload = () => {
            printWindow.print();
            // Close the window after printing
            setTimeout(() => {
              printWindow.close();
              window.URL.revokeObjectURL(url);
            }, 1000);
          };
        }
      } else {
        toast({
          title: "Erreur",
          description: "Impossible d'imprimer la facture",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Erreur réseau lors de l'impression",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Suivi des envois</h1>
      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2"><FileText className="h-5 w-5" />Envois</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={async () => {
              setLoading(true);
              const token = localStorage.getItem("token");
              if (token) {
                try {
                  const res = await fetch("http://localhost:8000/api/v1/sends/?limit=200", { headers: { Authorization: `Bearer ${token}` } });
                  if (res.ok) setSends(await res.json());
                } catch (e) {
                  toast({ title: "Erreur", description: "Impossible de rafraîchir", variant: "destructive" });
                }
              }
              setLoading(false);
            }}>
              <RefreshCw className="h-4 w-4 mr-1" /> Rafraîchir
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Id</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Nb bulletins</TableHead>
                <TableHead>Prix/unité</TableHead>
                <TableHead>Montant</TableHead>
                <TableHead>Facture</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sends.map((s) => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium">{s.id}</TableCell>
                  <TableCell>{new Date(s.created_at).toLocaleString()}</TableCell>
                  <TableCell>{s.nb_bulletins}</TableCell>
                  <TableCell>{s.price_per_bulletin.toFixed(2)} {s.pricing_plan?.currency || 'EUR'}</TableCell>
                  <TableCell>{s.total_amount.toFixed(2)} {s.pricing_plan?.currency || 'EUR'}</TableCell>
                  <TableCell>
                    {s.invoice_path ? (
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => handleDownload(s)}>
                          <Download className="h-4 w-4 mr-2" /> Télécharger
                        </Button>
                        <Button size="sm" onClick={() => handlePrint(s)}>
                          <Printer className="h-4 w-4 mr-2" /> Imprimer
                        </Button>
                      </div>
                    ) : (
                      <span className="text-sm text-muted-foreground">Non générée</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default Envois;
