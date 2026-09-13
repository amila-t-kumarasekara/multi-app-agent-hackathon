import type { ReactNode } from "react";
import { NewRunModal } from "../ui/NewRunModal";
import { MainHeader } from "./MainHeader";
import { Sidebar } from "./Sidebar";

type LeadTriageShellProps = {
  children: ReactNode;
};

export function LeadTriageShell({ children }: LeadTriageShellProps) {
  return (
    <div className="ltc-shell">
      <Sidebar />
      <main className="ltc-main">
        <MainHeader />
        <div className="ltc-body">{children}</div>
        <NewRunModal />
      </main>
    </div>
  );
}
