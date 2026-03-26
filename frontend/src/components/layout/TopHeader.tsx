import { Bell, Search } from "lucide-react";

export function TopHeader() {
  return (
    <header className="h-16 border-b border-border bg-card flex items-center">
      <div className="relative flex-1 h-full">
        <Search className="absolute left-6 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          className="h-full w-full bg-transparent pl-14 pr-4 text-sm focus:outline-none"
        />
      </div>
      <div className="flex items-center gap-4 px-6">
        <button className="p-2 rounded-md hover:bg-accent">
          <Bell className="h-5 w-5 text-muted-foreground" />
        </button>
        <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
          <span className="text-xs font-medium text-primary-foreground">U</span>
        </div>
      </div>
    </header>
  );
}
