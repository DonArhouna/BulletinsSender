import { useEffect, useState, useCallback } from "react";
import { Upload, Send, History, User, Settings, RefreshCw, Loader2, CheckCircle2, FileText, FolderOpen, Download } from "lucide-react";
import logo from "@/assets/logo.svg";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import UserDetailsDialog from "@/components/UserDetailsDialog";
import ChangePasswordDialog from "@/components/ChangePasswordDialog";
import { Alert, AlertDescription } from "@/components/ui/alert";

const Client = () => {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [subject, setSubject] = useState("Votre bulletin de salaire");
  const [userDetailsOpen, setUserDetailsOpen] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFiles(e.target.files);
  };

  const handleSend = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      toast({
        title: "Fichiers requis",
        description: "Veuillez sélectionner les fichiers PDF des bulletins.",
        variant: "destructive",
      });
      return;
    }

    if (!email) {
      toast({
        title: "Email requis",
        description: "Veuillez saisir votre email.",
        variant: "destructive",
      });
      return;
    }

    setIsSending(true);

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        toast({
          title: "Erreur d'authentification",
          description: "Veuillez vous reconnecter.",
          variant: "destructive",
        });
        setIsSending(false);
        return;
      }

      const formData = new FormData();
      for (let i = 0; i < selectedFiles.length; i++) {
        formData.append("files", selectedFiles[i]);
      }
      formData.append("sender_email", email);
      formData.append("subject", subject);
      formData.append("message", message || "Veuillez trouver ci-joint votre bulletin de salaire.");

      const response = await fetch("http://localhost:8000/api/v1/send-bulletins", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();

        // Message de succès stylé
        toast({
          title: (
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <span>Envoi réussi !</span>
            </div>
          ) as unknown as React.ReactNode,
          description: (
            <div className="space-y-2 mt-2">
              <p className="font-semibold">
                ✅ {result.successful_sends} email(s) envoyé(s) avec succès
              </p>
              {result.failed_sends > 0 && (
                <p className="text-orange-600">
                  ⚠️ {result.failed_sends} échec(s)
                </p>
              )}
              <p className="text-sm text-muted-foreground">
                Total : {result.total_files} fichier(s) traité(s)
              </p>
            </div>
          ) as unknown as React.ReactNode,
          duration: 5000,
        });

        // Reset form
        setSelectedFiles(null);
        setEmail("");
        setMessage("");
        setSubject("Votre bulletin de salaire");
        // Reset file input
        const fileInput = document.getElementById("folder-selector") as HTMLInputElement;
        if (fileInput) fileInput.value = "";
        // Rafraîchit l'historique immédiatement après un envoi réussi
        fetchHistoryPeriods();
      } else {
        const error = await response.json();
        toast({
          title: "Erreur",
          description: error.detail || "Erreur lors de l'envoi des bulletins",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Erreur lors de l'envoi:", error);
      toast({
        title: "Erreur réseau",
        description: "Impossible de contacter le serveur.",
        variant: "destructive",
      });
    } finally {
      setIsSending(false);
    }
  };

  const [historyPeriods, setHistoryPeriods] = useState<
    { period: string; date_time: string; bulletins_count: number; status_summary: string }[]
  >([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  interface UserSend { id:number; nb_bulletins:number; price_per_bulletin:number; total_amount:number; pricing_plan_id?:number|null; pricing_plan?:{currency?:string}; invoice_path?:string|null; created_at:string }
  const [userSends, setUserSends] = useState<UserSend[]>([]);
  const [isLoadingSends, setIsLoadingSends] = useState(false);

  const fetchUserSends = () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    setIsLoadingSends(true);
    fetch("http://localhost:8000/api/v1/sends/", { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => res.json())
      .then((data) => setUserSends(data))
      .catch(() => {})
      .finally(() => setIsLoadingSends(false));
  };

  const fetchHistoryPeriods = useCallback(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    setIsLoadingHistory(true);
    fetch("http://localhost:8000/api/v1/email-history-periods?limit=3", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        const txt = await res.text();
        let json: unknown = null;
        try {
          json = txt ? JSON.parse(txt) : null;
        } catch (e) {
          console.error("Erreur JSON parsing for history response:", e, txt);
        }

        if (!res.ok) {
          // try to extract message
          const detail = json?.detail || json?.message || txt;
          throw new Error(`HTTP ${res.status} - ${detail}`);
        }

  // Normaliser la forme: acceptons soit une liste directe, soit { results: [] } ou { data: [] }
  const parsed = json as unknown as { results?: unknown[]; data?: unknown[] } | null;
  const normalized = parsed && (parsed.results || parsed.data) ? (parsed.results || parsed.data) : json;
        return normalized;
      })
      .then((data) => {
        console.log("Historique reçu (normalisé):", data);
        if (Array.isArray(data)) {
          setHistoryPeriods(data);
        } else if (data && typeof data === "object") {
          // si l'API renvoie un objet avec clés inattendues
          const obj = data as unknown as { items?: unknown[]; periods?: unknown[] } | null;
          const arr = (obj && (obj.items || obj.periods)) || [];
          setHistoryPeriods(
            Array.isArray(arr)
              ? (arr as unknown as { period: string; date_time: string; bulletins_count: number; status_summary: string }[])
              : []
          );
        } else {
          setHistoryPeriods([]);
        }
      })
      .catch((error) => {
        console.error("Erreur lors du chargement de l'historique:", error);
        toast({
          title: "Erreur lors du chargement",
          description: error?.message || "Impossible de charger l'historique des envois",
          variant: "destructive",
        });
      })
    .finally(() => setIsLoadingHistory(false));
  }, [toast]);

  useEffect(() => {
    fetchHistoryPeriods();
    fetchUserSends();
  }, [fetchHistoryPeriods]);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="h-16 flex items-center justify-between px-6 sticky top-0 z-20 bg-sky-100/90 backdrop-blur border-b border-sky-200 shadow-sm">
        <div className="flex items-center gap-3">
          <img src={logo} alt="Logo" className="h-12 w-12" />
          <div className="hidden sm:block">
            <h1 className="text-base font-semibold text-sky-900">Bulletin Sender</h1>
            <p className="text-xs text-sky-800/80">Espace Client</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="hover:bg-sky-200 rounded-full" onClick={() => setChangePasswordOpen(true)}>
            <Settings className="h-5 w-5 text-sky-900" />
          </Button>
          <Avatar className="h-9 w-9 ring-2 ring-white shadow cursor-pointer" onClick={() => setUserDetailsOpen(true)}>
            <AvatarFallback className="bg-sky-700 text-white">
              <User className="h-4 w-4" />
            </AvatarFallback>
          </Avatar>
        </div>
      </header>

      <UserDetailsDialog open={userDetailsOpen} onOpenChange={setUserDetailsOpen} />
      <ChangePasswordDialog open={changePasswordOpen} onOpenChange={setChangePasswordOpen} />

      <div className="p-4 md:p-6">
        <div className="max-w-4xl mx-auto space-y-6">

        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900">
              <Upload className="h-5 w-5 text-sky-700" />
              Envoyer les bulletins
            </CardTitle>
            <CardDescription>
              Sélectionnez le dossier contenant les bulletins PDF à envoyer
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="folder-selector">Choisir le dossier</Label>
              <div className="relative">
                <input
                  id="folder-selector"
                  type="file"
                  multiple
                  webkitdirectory=""
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                <div className="h-32 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors flex flex-col items-center justify-center gap-3 cursor-pointer">
                  <Upload className="h-8 w-8 text-sky-600" />
                  <div className="text-center">
                    <p className="text-sm font-medium text-slate-700">Cliquez pour sélectionner un dossier</p>
                    <p className="text-xs text-slate-500">Ou glissez-déposez vos fichiers PDF ici</p>
                  </div>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Sélectionnez un dossier contenant uniquement des fichiers PDF avec les informations d'email et mot de passe à la fin.
              </p>

              {/* Composant stylé pour afficher les fichiers sélectionnés */}
              {selectedFiles && selectedFiles.length > 0 && (
                <Alert className="border-sky-200 bg-sky-50">
                  <FolderOpen className="h-4 w-4 text-sky-600" />
                  <AlertDescription>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-sky-600" />
                        <span className="font-semibold text-sky-900">
                          {selectedFiles.length} fichier(s) PDF sélectionné(s)
                        </span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedFiles(null);
                          const fileInput = document.getElementById("folder-selector") as HTMLInputElement;
                          if (fileInput) fileInput.value = "";
                        }}
                        className="h-7 text-xs hover:bg-sky-100"
                      >
                        Annuler
                      </Button>
                    </div>
                    <div className="mt-2 text-xs text-sky-700">
                      Prêt à envoyer les bulletins aux destinataires
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="sender-email">Email de l'envoyeur</Label>
                <Input
                  id="sender-email"
                  type="email"
                  placeholder="votre.email@entreprise.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="rounded-xl border-slate-300 focus:ring-sky-300"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="subject">Sujet de l'email</Label>
                <Input
                  id="subject"
                  type="text"
                  placeholder="Votre bulletin de salaire"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="rounded-xl border-slate-300 focus:ring-sky-300"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">Message personnalisé</Label>
                <Textarea
                  id="message"
                  placeholder="Exemple : Merci de recevoir ci-joint votre bulletin de salaire"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={4}
                  className="rounded-xl border-slate-300 focus:ring-sky-300"
                />
              </div>
            </div>

            <Button
              onClick={handleSend}
              disabled={isSending}
              className="w-full rounded-xl bg-sky-600 hover:bg-sky-700 disabled:opacity-70"
              size="lg"
            >
              {isSending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Envoi en cours...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Envoyer les bulletins
                </>
              )}
            </Button>

            {/* Indicateur de progression pendant l'envoi */}
            {isSending && (
              <Alert className="border-blue-200 bg-blue-50">
                <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                <AlertDescription>
                  <div className="space-y-1">
                    <p className="font-semibold text-blue-900">
                      Envoi des bulletins en cours...
                    </p>
                    <p className="text-xs text-blue-700">
                      Veuillez patienter pendant le traitement et l'envoi des emails.
                    </p>
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-slate-900">
                <History className="h-5 w-5 text-sky-700" />
                Historique des envois
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchHistoryPeriods}
                disabled={isLoadingHistory}
                className="rounded-lg"
              >
                <RefreshCw className="h-4 w-4 mr-1" /> {isLoadingHistory ? "Chargement…" : "Rafraîchir"}
              </Button>
            </div>
            <CardDescription>
              Historique groupé par période d'activité
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {historyPeriods.length > 0 ? (
                historyPeriods.map((period, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 bg-muted rounded-lg border border-slate-200"
                  >
                    <div className="flex flex-col space-y-1">
                      <span className="font-semibold text-slate-900">{period.period}</span>
                      <span className="text-sm text-slate-600">
                        Dernière activité : {period.date_time}
                      </span>
                      <span className="text-sm text-slate-500">
                        {period.status_summary}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-sky-700">
                        {period.bulletins_count}
                      </div>
                      <div className="text-xs text-slate-500">
                        bulletins
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500">
                  {isLoadingHistory ? (
                    <p>Chargement de l’historique…</p>
                  ) : (
                    <>
                      <History className="h-12 w-12 mx-auto mb-3 opacity-50" />
                      <p>Aucun historique d'envoi disponible</p>
                    </>
                  )}
                </div>
              )}
              {historyPeriods.length === 3 && (
                <div className="text-center py-2">
                  <p className="text-sm text-slate-500">
                    Affichage des 3 dernières périodes d'activité
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-slate-900">
                <FileText className="h-5 w-5 text-sky-700" />
                Détails des envois
              </CardTitle>
              <Button variant="outline" size="sm" onClick={() => fetchUserSends()}>
                <RefreshCw className="h-4 w-4 mr-1" /> Rafraîchir
              </Button>
            </div>
            <CardDescription>
              Historique détaillé de vos envois avec montant et facture
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {userSends.length > 0 ? (
                userSends.slice(0, 3).map((s) => (
                  <div key={s.id} className="flex items-center justify-between p-4 bg-muted rounded-lg border border-slate-200">
                    <div className="flex flex-col">
                      <span className="font-semibold text-slate-900">Envoi #{s.id} — {new Date(s.created_at).toLocaleString()}</span>
                      <span className="text-sm text-slate-600">{s.nb_bulletins} bulletin(s) — Forfait: {s.pricing_plan_id || '—'}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-sky-700">{s.total_amount.toFixed(2)} {s.pricing_plan?.currency || 'EUR'}</div>
                      <div className="text-sm text-slate-600">{s.price_per_bulletin.toFixed(2)} {s.pricing_plan?.currency || 'EUR'} / bulletin</div>
                      <div className="mt-2 flex gap-2 justify-end">
                        {s.invoice_path ? (
                          <Button size="sm" onClick={async () => {
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
                                a.download = `facture_${s.id}.pdf`;
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
                          }}>
                            <Download className="h-4 w-4 mr-2" /> Facture
                          </Button>
                        ) : (
                          <span className="text-sm text-muted-foreground">Facture en cours</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500">
                  {isLoadingSends ? (
                    <p>Chargement des envois…</p>
                  ) : (
                    <p>Aucun envoi trouvé</p>
                  )}
                </div>
              )}
              {userSends.length > 3 && (
                <div className="text-center py-2">
                  <p className="text-sm text-slate-500">
                    Affichage des 3 derniers envois sur {userSends.length} au total
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
        </div>
      </div>
    </div>
  );
};

export default Client;
