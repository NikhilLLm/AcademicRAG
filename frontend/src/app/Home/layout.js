import Sidebar from "./components/Sidebar";
import "@/app/Home/local.css";
export default function DashboardLayout({ children }) {
  return (
    <div className="flex min-h-screen bg-[#0B0E1A]">
      <Sidebar />

      <main className="flex-1 bg-[#1a1a1a] p-6 md:p-8">
        {children}
      </main>
    </div>
  );
}
