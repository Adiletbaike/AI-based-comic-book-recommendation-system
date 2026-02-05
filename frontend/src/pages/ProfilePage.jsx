import { useAuth } from "../hooks/useAuth";

const ProfilePage = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  const firstLetter = user.email?.charAt(0).toUpperCase();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Profile</h1>
        <p className="text-sm text-slate-500">Your account details.</p>
      </div>

      <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-[#171717]">
        {/* LEFT */}
        <div className="flex items-center gap-4">
          {/* AVATAR LETTER */}
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 text-xl font-bold uppercase text-white">
            {firstLetter}
          </div>

          <div>
            <p className="text-lg font-semibold">{user.username}</p>
            <p className="text-sm text-slate-500">{user.email}</p>
          </div>
        </div>

        {/* RIGHT */}
        <button
          onClick={logout}
          className="rounded-lg border border-red-500 px-4 py-2 text-sm font-medium text-red-500 transition hover:bg-red-500 hover:text-white"
        >
          Logout
        </button>
      </div>
    </div>
  );
};

export default ProfilePage;
