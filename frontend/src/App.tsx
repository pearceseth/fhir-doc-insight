import { useState } from "react";
import { Dashboard } from "./pages/Dashboard";
import { Analytics } from "./pages/Analytics";
import { Assistant } from "./pages/Assistant";
import { EncounterDetail } from "./pages/EncounterDetail";
import { AppLayout } from "./components/layout/AppLayout";

type Tab = "dashboard" | "analytics" | "assistant";

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [selectedEncounterId, setSelectedEncounterId] = useState<string | null>(null);

  function handleSelectEncounter(encounterId: string) {
    setSelectedEncounterId(encounterId);
  }

  function handleBackToList() {
    setSelectedEncounterId(null);
  }

  function handleTabChange(tab: Tab) {
    setSelectedEncounterId(null);
    setActiveTab(tab);
  }

  function renderContent() {
    switch (activeTab) {
      case "dashboard":
        return selectedEncounterId ? (
          <EncounterDetail encounterId={selectedEncounterId} onBack={handleBackToList} />
        ) : (
          <Dashboard onSelectEncounter={handleSelectEncounter} />
        );
      case "analytics":
        return <Analytics />;
      case "assistant":
        return <Assistant />;
    }
  }

  return (
    <AppLayout activeNav={activeTab} onNavChange={handleTabChange}>
      {renderContent()}
    </AppLayout>
  );
}

export default App;
