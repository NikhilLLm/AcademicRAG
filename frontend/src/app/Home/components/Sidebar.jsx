"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  FileText,
  History,
  Home,
  MessageSquare,
  Menu,
  X,
  Search,
  LogOut, // Added LogOut icon
} from "lucide-react";
import { useState, useEffect } from "react";
import { getUserInfo } from "@/lib/api_call";


export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter(); // Initialize router
  const [open, setOpen] = useState(false);
  const [user, setUser] = useState(null);
  const navItems = [
    { name: "Home", href: "/Home", icon: Home },
    { name: "My Notes", href: "/Home/notes", icon: FileText },
    { name: "Chat", href: "/Home/chat", icon: MessageSquare },
    { name: "History", href: "/Home/history", icon: History },
  ];

  useEffect(() => {
    //token is in cookies
    console.log(getUserInfo())
    getUserInfo().then((res) => {
      setUser(res)
    })
  }, [])

  // Logout handler
  const handleLogout = () => {
    localStorage.removeItem("auth_token"); // Clear token
    router.push("/"); // Redirect to landing page
  };

  return (
    <>
      {/* Mobile Hamburger */}
      <button
        className="md:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-black text-white"
        onClick={() => setOpen(true)}
      >
        <Menu className="w-6 h-6" />
      </button>

      {/* Overlay (mobile) */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          bg-#18181b text-white w-64
          px-6 py-8 flex flex-col justify-between
          transition-transform duration-300
      
          fixed top-0 left-0 h-screen z-50
          md:static md:h-auto md:z-auto
      
          ${open ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0
        `}
      >
        {/* Close button (mobile) */}
        <button
          className="md:hidden absolute top-4 right-4"
          onClick={() => setOpen(false)}
        >
          <X className="w-6 h-6" />
        </button>

        {/* Logo */}
        <div>
          <h2 className="text-2xl font-bold mb-10 tracking-tight">
            Paper<span className="text-blue-500">Semantic</span>
          </h2>

          {/* Navigation */}
          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={`flex items-center gap-3 px-4 py-2 rounded-md text-sm font-medium transition-colors
                  ${isActive
                      ? "bg-blue-600 text-white"
                      : "text-gray-400 hover:bg-[#1f1f22]"
                    }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Profile & Logout */}
        <div>
          <div className="flex items-center justify-between p-3 bg-[#121524] rounded-lg">
            {/* User Info */}
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-9 h-9 bg-blue-600 rounded-full flex-shrink-0 flex items-center justify-center">
                <span className="text-sm font-semibold">
                  {user?.email?.split("@")[0].slice(0, 1).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {user?.email?.split("@")[0]}
                </p>
                <p className="text-xs text-gray-400 truncate">
                  {user?.email}
                </p>
              </div>
            </div>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="ml-2 p-1.5 text-gray-400 hover:text-white hover:bg-red-900/30 hover:text-red-400 rounded-md transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
