import { NavLink } from "react-router-dom";

const Sidebar = () => {
  return (
    <aside className="hidden w-60 border-r border-slate-200 bg-white p-4 md:block dark:border-slate-800 dark:bg-[#171717]">
      <nav className="flex flex-col gap-2 text-sm">
        <NavLink
          to="/"
          className={({ isActive }) =>
            `rounded px-3 py-2 ${
              isActive
                ? "bg-slate-200 text-slate-900 dark:bg-slate-800 dark:text-white"
                : "text-slate-600 hover:bg-slate-200 dark:text-slate-300 dark:hover:bg-slate-800"
            }`
          }
        >
          Home
        </NavLink>
        <NavLink
          to="/library"
          className={({ isActive }) =>
            `rounded px-3 py-2 ${
              isActive
                ? "bg-slate-200 text-slate-900 dark:bg-slate-800 dark:text-white"
                : "text-slate-600 hover:bg-slate-200 dark:text-slate-300 dark:hover:bg-slate-800"
            }`
          }
        >
          Library
        </NavLink>
        <NavLink
          to="/trash"
          className={({ isActive }) =>
            `rounded px-3 py-2 ${
              isActive
                ? "bg-slate-200 text-slate-900 dark:bg-slate-800 dark:text-white"
                : "text-slate-600 hover:bg-slate-200 dark:text-slate-300 dark:hover:bg-slate-800"
            }`
          }
        >
          Trash
        </NavLink>
        <NavLink
          to="/profile"
          className={({ isActive }) =>
            `rounded px-3 py-2 ${
              isActive
                ? "bg-slate-200 text-slate-900 dark:bg-slate-800 dark:text-white"
                : "text-slate-600 hover:bg-slate-200 dark:text-slate-300 dark:hover:bg-slate-800"
            }`
          }
        >
          Profile
        </NavLink>
      </nav>
    </aside>
  );
};

export default Sidebar;
