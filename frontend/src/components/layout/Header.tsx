"use client";

import React from "react";
import { usePathname } from "next/navigation";
import UserMenu from "@/components/layout/UserMenu";
import { Menu } from "lucide-react";

interface HeaderProps {
  onOpenMobileMenu: () => void;
}

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/documents": "Documents",
  "/profile": "User Profile",
  "/settings": "Settings",
};

export function Header({ onOpenMobileMenu }: HeaderProps) {
  const pathname = usePathname();
  const pageTitle = PAGE_TITLES[pathname] || "Dashboard";

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-800 bg-slate-950/80 px-4 sm:px-6 backdrop-blur-md">
      <div className="flex items-center space-x-3">
        <button
          onClick={onOpenMobileMenu}
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-900 hover:text-white md:hidden"
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <h1 className="text-lg font-bold text-white tracking-tight sm:text-xl">
          {pageTitle}
        </h1>
      </div>

      <div className="flex items-center space-x-4">
        <UserMenu />
      </div>
    </header>
  );
}

export default Header;
