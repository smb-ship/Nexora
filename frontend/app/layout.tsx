import "./globals.css";
import type { Metadata } from "next";
import { Geist } from "next/font/google";
import Script from "next/script";
import { AuthProvider } from "@/lib/auth-context";

const geist = Geist({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Nexora",
  description: "AI Customer Support Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={geist.className}>
        <AuthProvider>{children}</AuthProvider>

        <Script
          src="/chat-widget.js"
          strategy="afterInteractive"
          data-public-key="widget_8W9p0TP3n11yzm-wTejGgg"
          data-api-base="http://localhost:8000/api/v1"
        />
      </body>
    </html>
  );
}