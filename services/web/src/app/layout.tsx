import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "./components/ui/sonner";

export const metadata: Metadata = {
  title: "Artemis — AI Job Copilot",
  description: "Your AI-powered job search and application assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        {children}
        <Toaster position="top-right" richColors />
      </body>
    </html>
  );
}
