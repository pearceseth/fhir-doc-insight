import { Sidebar, type NavItem } from "./Sidebar";
import { TopHeader } from "./TopHeader";

interface AppLayoutProps {
  activeNav: NavItem;
  onNavChange: (nav: NavItem) => void;
  children: React.ReactNode;
}

export function AppLayout({ activeNav, onNavChange, children }: AppLayoutProps) {
  return (
    <div className="flex h-screen">
      <Sidebar activeNav={activeNav} onNavChange={onNavChange} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopHeader />
        <main className="flex-1 overflow-auto bg-background p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
