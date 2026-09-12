import React from "react";
import { AppProvider, useApp } from "./store/AppContext";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { DashboardView } from "./components/DashboardView";
import { UploadView } from "./components/UploadView";
import { DatasetManagerView } from "./components/DatasetManagerView";
import { PreprocessingView } from "./components/PreprocessingView";
import { InspectionPipelineView } from "./components/InspectionPipelineView";
import { ModelTrainingView } from "./components/ModelTrainingView";
import { ModelManagementView } from "./components/ModelManagementView";
import { ReportsView } from "./components/ReportsView";
import { MaintenanceTicketsView } from "./components/MaintenanceTicketsView";
import { LogsView } from "./components/LogsView";
import { SettingsView } from "./components/SettingsView";

function MainLayout() {
  const { activeTab } = useApp();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-slate-950">
          {activeTab === "dashboard" && <DashboardView />}
          {activeTab === "upload" && <UploadView />}
          {activeTab === "datasets" && <DatasetManagerView />}
          {activeTab === "preprocess" && <PreprocessingView />}
          {activeTab === "pipeline" && <InspectionPipelineView />}
          {activeTab === "training" && <ModelTrainingView />}
          {activeTab === "models" && <ModelManagementView />}
          {activeTab === "reports" && <ReportsView />}
          {activeTab === "tickets" && <MaintenanceTicketsView />}
          {activeTab === "logs" && <LogsView />}
          {activeTab === "settings" && <SettingsView />}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <MainLayout />
    </AppProvider>
  );
}
