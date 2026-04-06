import type { Metadata } from "next";
import { Sora, DM_Mono } from "next/font/google";
import "./globals.css";

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sora",
  display: "swap",
});

const dmMono = DM_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-dm-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    template: "%s | Win Path",
    default: "Win Path | Your Team's Roadmap to the IPL Trophy",
  },
  description:
    "IPL qualification path predictor. Pick your team, see exactly what needs to happen for them to win the IPL. Based on 50,000 Monte Carlo simulations.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://ipl-tracker-mu.vercel.app"
  ),
  openGraph: {
    title: "Win Path | Your Team's Roadmap to the IPL Trophy",
    description:
      "Pick your team. We'll show you the path to the IPL trophy.",
    siteName: "Win Path by Ascnd",
    type: "website",
    locale: "en_IN",
  },
  twitter: {
    card: "summary_large_image",
    title: "Win Path | Your Team's Roadmap to the IPL Trophy",
    description:
      "Pick your team. We'll show you the path to the IPL trophy.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${sora.variable} ${dmMono.variable}`}>
      <body className="font-sans bg-bg text-text antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
