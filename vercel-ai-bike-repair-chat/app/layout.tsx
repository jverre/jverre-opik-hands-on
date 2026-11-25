import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Spoke - Cobblestone Cycle Co-op",
  description: "Streaming bike-repair workshop assistant, traced with Opik",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          background: "#f4f6f1",
          color: "#1d2419",
        }}
      >
        {children}
      </body>
    </html>
  );
}
