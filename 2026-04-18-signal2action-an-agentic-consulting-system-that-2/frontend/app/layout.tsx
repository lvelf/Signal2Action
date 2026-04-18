import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Signal2Action",
  description: "Agentic consulting system that turns ambiguous enterprise signals into action plans."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
