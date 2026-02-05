import { Link, Navigate } from "react-router-dom";
import Login from "../components/Auth/Login";
import { useAuth } from "../hooks/useAuth";

const LoginPage = () => {
  const { user, isReady } = useAuth();
  if (isReady && user) return <Navigate to="/" replace />;

  return (
    <div className="min-h-screen bg-[#0b1b3b]">
      <div className="relative min-h-screen">
        <img
          src="/marvel-background-web.webp"
          alt="Marvel background"
          className="absolute inset-0 h-full w-full object-cover opacity-90"
        />
        <div className="absolute inset-0 bg-[#0b1b3b]/70" />

        <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-10">
          <div className="w-full max-w-md rounded-2xl bg-white px-8 py-8 shadow-xl">
            <div className="mb-6 text-center">
              <div className="mx-auto mb-4 flex h-12 w-36 items-center justify-center rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 shadow-lg shadow-blue-600/30">
                <span className="text-lg font-extrabold tracking-widest text-white">
                  COMIC<span className="text-black">AI</span>
                </span>
              </div>
              <h1 className="text-xl font-semibold">Enter your email to continue</h1>
              <p className="mt-2 text-sm text-slate-500">
                Log in to ComicAI with your account. If you don&apos;t have one, you&apos;ll be
                prompted to create it.
              </p>
            </div>

            <Login />

            <div className="mt-6 space-y-2 text-center text-sm">
              <p className="text-slate-500">
                No account?{" "}
                <Link to="/register" className="font-medium text-blue-600">
                  Register
                </Link>
              </p>
              <Link to="/forgot-password" className="font-medium text-blue-600">
                Forgot password?
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
