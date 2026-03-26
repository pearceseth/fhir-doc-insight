import { LayoutDashboard, ChartNetwork } from "lucide-react";
import { cn } from "@/lib/utils";

type NavItem = "dashboard" | "agentic";

interface SidebarProps {
  activeNav: NavItem;
  onNavChange: (nav: NavItem) => void;
}

const navItems: { id: NavItem; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "agentic", label: "Agentic Mode", icon: ChartNetwork },
];

export function Sidebar({ activeNav, onNavChange }: SidebarProps) {
  return (
    <aside className="w-64 h-screen bg-sidebar border-r border-sidebar-border flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-sidebar-border">
        <h1 className="text-lg font-semibold text-sidebar-foreground">FHIR Insight</h1>
      </div>
      <nav className="flex-1 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeNav === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavChange(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-6 py-3 text-sm transition-colors",
                "border-l-2 border-transparent",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground border-l-primary"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
