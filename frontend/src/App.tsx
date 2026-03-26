import { useState } from "react";
import { Dashboard } from "./pages/Dashboard";
import { Analytics } from "./pages/Analytics";
import { EncounterDetail } from "./pages/EncounterDetail";
import { AppLayout } from "./components/layout/AppLayout";

type Tab = "dashboard" | "analytics";

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

  return (
    <AppLayout activeNav={activeTab} onNavChange={handleTabChange}>
      {activeTab === "dashboard" ? (
        selectedEncounterId ? (
          <EncounterDetail encounterId={selectedEncounterId} onBack={handleBackToList} />
        ) : (
          <Dashboard onSelectEncounter={handleSelectEncounter} />
        )
      ) : (
        <Analytics />
      )}
    </AppLayout>
  );
}

export default App;
