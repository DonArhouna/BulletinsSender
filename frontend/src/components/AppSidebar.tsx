import { LayoutDashboard, Users, CreditCard, Settings, Package } from "lucide-react";
import { NavLink } from "react-router-dom";
import logo from "@/assets/logo.svg";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

const menuItems = [
  { title: "Tableau de bord", url: "/admin", icon: LayoutDashboard },
  { title: "Abonnements", url: "/admin/abonnements", icon: CreditCard },
  { title: "Forfaits", url: "/admin/forfaits", icon: Package },
  { title: "Utilisateurs", url: "/admin/utilisateurs", icon: Users },
  { title: "Envois", url: "/admin/envois", icon: Package },
  { title: "Paramètres", url: "/admin/parametres", icon: Settings },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";

  return (
    <Sidebar className={(collapsed ? "w-14" : "w-64") + " text-white"} collapsible="icon" style={{ backgroundColor: "#2596be" }}>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="px-4 pt-8 pb-6 flex justify-center">
            <img src={logo} alt="Logo" className={(collapsed ? "h-16 w-16" : "h-24 w-24") + " rounded-[50%]"} />
          </SidebarGroupLabel>
          <SidebarGroupContent className="mt-6">
            <SidebarMenu className="space-y-2">
              {menuItems.map((item, idx) => (
                <SidebarMenuItem key={item.title} className={idx === 0 ? "mt-2" : undefined}>
                  <SidebarMenuButton asChild className="text-white/95 hover:bg-white/15 focus:bg-white/20">
                    <NavLink
                      to={item.url}
                      end
                      className={({ isActive }) =>
                        (isActive
                          ? "bg-white/20 text-white font-medium"
                          : "") + " rounded-md"
                      }
                    >
                      <item.icon className="h-5 w-5" />
                      {!collapsed && <span className="text-[15px]">{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
