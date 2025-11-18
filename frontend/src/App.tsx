import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Client from "./pages/Client";
import Abonnements from "./pages/Abonnements";
import Forfaits from "./pages/Forfaits";
import Utilisateurs from "./pages/Utilisateurs";
import Envois from "./pages/Envois";
import Parametres from "./pages/Parametres";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import AdminLayout from "./components/AdminLayout";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/client" element={<Client />} />
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="abonnements" element={<Abonnements />} />
            <Route path="forfaits" element={<Forfaits />} />
            <Route path="envois" element={<Envois />} />
            <Route path="utilisateurs" element={<Utilisateurs />} />
            <Route path="parametres" element={<Parametres />} />
          </Route>
          <Route path="/" element={<Login />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
