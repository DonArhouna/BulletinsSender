import { useState } from "react";
import { Outlet } from "react-router-dom";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "./AppSidebar";
import { Bell, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import UserDetailsDialog from "./UserDetailsDialog";

const AdminLayout = () => {
  const [userDetailsOpen, setUserDetailsOpen] = useState(false);

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-slate-50">
        <AppSidebar />
        <div className="flex-1 flex flex-col">
          <header className="h-16 flex items-center justify-between px-4 sticky top-0 z-20 bg-sky-100/90 backdrop-blur border-b border-sky-200 shadow-sm">
            <div className="flex items-center gap-2 text-sky-900">
              <SidebarTrigger className="text-sky-900" />
              <span className="font-semibold">Panneau Super Admin</span>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" className="hover:bg-sky-200 rounded-full">
                <Bell className="h-5 w-5 text-sky-900" />
              </Button>
              <Avatar className="h-9 w-9 ring-2 ring-white shadow cursor-pointer" onClick={() => setUserDetailsOpen(true)}>
                <AvatarFallback className="bg-sky-700 text-white">
                  <User className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            </div>
          </header>
          <main className="flex-1 overflow-auto p-4 md:p-6">
            <Outlet />
          </main>
        </div>
      </div>
      <UserDetailsDialog open={userDetailsOpen} onOpenChange={setUserDetailsOpen} />
    </SidebarProvider>
  );
};

export default AdminLayout;
