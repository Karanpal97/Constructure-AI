import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Constructure AI - Email Assistant",
  description: "AI-powered email assistant that helps you manage your inbox with natural language commands",
  keywords: ["email", "AI", "assistant", "gmail", "automation"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-slate-950 antialiased">
        {children}
      </body>
    </html>
  );
}
