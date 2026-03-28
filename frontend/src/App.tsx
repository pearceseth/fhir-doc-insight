import { useState } from "react";
import { Dashboard } from "./pages/Dashboard";
import { Analytics } from "./pages/Analytics";
import { Assistant } from "./pages/Assistant";
import { EncounterDetail } from "./pages/EncounterDetail";
import { AppLayout } from "./components/layout/AppLayout";
import type { Encounter } from "./api/fhir";

type Tab = "dashboard" | "analytics" | "assistant";

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [selectedEncounter, setSelectedEncounter] = useState<Encounter | null>(null);

  function handleSelectEncounter(encounter: Encounter) {
    setSelectedEncounter(encounter);
  }

  function handleBackToList() {
    setSelectedEncounter(null);
  }

  function handleTabChange(tab: Tab) {
    setSelectedEncounter(null);
    setActiveTab(tab);
  }

  function renderContent() {
    switch (activeTab) {
      case "dashboard":
        return selectedEncounter ? (
          <EncounterDetail encounter={selectedEncounter} onBack={handleBackToList} />
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
