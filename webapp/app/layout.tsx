import type { Metadata } from "next";
import "./globals.css";
import "./styles/organic.css";
import "./styles/lead-triage.css";

export const metadata: Metadata = {
  title: "Furrow — Lead Triage Console",
  description: "Lead triage operations console for inbound agent runs.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
