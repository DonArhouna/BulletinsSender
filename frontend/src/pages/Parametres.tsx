import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Settings, Lock, UserX, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import ChangePasswordDialog from "@/components/ChangePasswordDialog";

const Parametres = () => {
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const { toast } = useToast();

  const handleBlockUser = () => {
    if (!userEmail) {
      toast({
        title: "Erreur",
        description: "Veuillez entrer un email utilisateur.",
        variant: "destructive",
      });
      return;
    }

    // TODO: Implémenter la logique de blocage
    toast({
      title: "Succès",
      description: `L'utilisateur ${userEmail} a été bloqué.`,
    });
    setUserEmail("");
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Paramètres</h1>
      
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-5 w-5" />
            Sécurité
          </CardTitle>
          <CardDescription>
            Gérez votre mot de passe et les paramètres de sécurité
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => setChangePasswordOpen(true)}>
            <Lock className="mr-2 h-4 w-4" />
            Changer le mot de passe
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Gestion des utilisateurs
          </CardTitle>
          <CardDescription>
            Bloquez ou débloquez des utilisateurs
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="user-email">Email de l'utilisateur</Label>
            <Input
              id="user-email"
              type="email"
              placeholder="utilisateur@example.com"
              value={userEmail}
              onChange={(e) => setUserEmail(e.target.value)}
            />
          </div>
          <Button onClick={handleBlockUser} variant="destructive">
            <UserX className="mr-2 h-4 w-4" />
            Bloquer l'utilisateur
          </Button>
        </CardContent>
      </Card>

      <ChangePasswordDialog open={changePasswordOpen} onOpenChange={setChangePasswordOpen} />
    </div>
  );
};

export default Parametres;
