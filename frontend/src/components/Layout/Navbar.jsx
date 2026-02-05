import { Link } from "react-router-dom";
import { Moon, Sun } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { useTheme } from "../../hooks/useTheme";
import { useEffect, useRef, useState } from "react";

const Navbar = () => {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();

  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Outside click handler
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <nav className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3 dark:border-slate-800 dark:bg-[#171717]">
      {/* LOGO */}
      <div className="flex items-center gap-2">
        <div className="flex h-12 w-36 items-center justify-center rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 shadow-lg shadow-blue-600/30">
          <span className="text-lg font-extrabold tracking-widest text-white">
            COMIC<span className="text-black">AI</span>
          </span>
        </div>
      </div>

      {/* RIGHT */}
      <div className="flex items-center gap-4">
        {/* THEME TOGGLE */}
        <button
          onClick={toggleTheme}
          className="rounded border border-slate-200 px-3 py-2 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* PROFILE */}
        {user && (
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setOpen((prev) => !prev)}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-sm font-bold uppercase text-white"
            >
              {user.email?.charAt(0)}
            </button>

            {open && (
              <div className="absolute right-0 top-11 z-50 min-w-[160px] rounded-xl border border-slate-200 bg-white p-2 shadow-lg dark:border-slate-700 dark:bg-slate-800">
                <Link
                  to="/profile"
                  onClick={() => setOpen(false)}
                  className="block rounded px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  Profile
                </Link>

                <button
                  onClick={() => {
                    setOpen(false);
                    logout();
                  }}
                  className="mt-1 w-full rounded bg-red-500 px-3 py-2 text-sm text-white hover:bg-red-600"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
