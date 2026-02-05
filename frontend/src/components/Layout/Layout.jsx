import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

const Layout = () => {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-[#0f0f0f] dark:text-slate-100">
      <Navbar />
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 bg-slate-50 px-6 py-6 dark:bg-[#0f0f0f]">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
