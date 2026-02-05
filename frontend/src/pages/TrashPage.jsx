import { useContext, useEffect, useMemo, useState } from "react";
import { RotateCcw, Trash2, X } from "lucide-react";
import { ComicContext } from "../context/ComicContext";
import { getLibrary } from "../services/library";

const TrashPage = () => {
  const ctx = useContext(ComicContext);
  if (!ctx) return null;

  const [query, setQuery] = useState("");
  const [remoteTrash, setRemoteTrash] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const runSearch = async (value) => {
    const term = value.trim();
    if (!term) {
      setRemoteTrash([]);
      setSearched(false);
      return;
    }
    setLoading(true);
    setSearched(true);
    try {
      const results = await getLibrary("trash", term);
      setRemoteTrash(results || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isActive = true;
    if (!query.trim()) {
      setRemoteTrash([]);
      setSearched(false);
      return;
    }
    const timer = setTimeout(async () => {
      if (!isActive) return;
      setLoading(true);
      setSearched(true);
      try {
        const results = await getLibrary("trash", query.trim());
        if (isActive) setRemoteTrash(results || []);
      } finally {
        if (isActive) setLoading(false);
      }
    }, 300);

    return () => {
      isActive = false;
      clearTimeout(timer);
    };
  }, [query]);

  const items = useMemo(() => {
    if (query.trim()) return remoteTrash;
    return ctx.trash;
  }, [query, remoteTrash, ctx.trash]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Trash</h1>
        <p className="text-sm text-slate-500">
          Restore items or permanently delete them from your account.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative w-full max-w-md">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && runSearch(query)}
            placeholder="Search by title, author, or genre..."
            className="w-full rounded-lg border border-slate-200 bg-transparent px-4 py-2 pr-10 text-sm text-slate-500 outline-none focus:border-blue-500"
          />
          {query && (
            <button
              onClick={() => {
                setQuery("");
                setRemoteTrash([]);
                setSearched(false);
              }}
              className="absolute right-2 top-2 rounded p-1 text-slate-400 hover:text-slate-600"
              aria-label="Clear search"
            >
              <X size={14} />
            </button>
          )}
        </div>
        {loading && <span className="text-xs text-slate-500">Searching...</span>}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {items.length === 0 && !searched && (
          <div className="rounded-xl border border-dashed border-slate-200 p-4 text-sm text-slate-400 dark:border-slate-700">
            Trash is empty.
          </div>
        )}
        {items.length === 0 && searched && (
          <div className="rounded-xl border border-dashed border-slate-200 p-4 text-sm text-slate-400 dark:border-slate-700">
            No results found.
          </div>
        )}

        {items.map((comic) => {
          const cover = comic.coverImage || comic.cover_image;
          return (
            <div
              key={comic.id}
              className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#171717]"
            >
              <div className="flex gap-3">
                {cover ? (
                  <img
                    src={cover}
                    alt={comic.title}
                    className="h-20 w-14 rounded object-cover"
                  />
                ) : (
                  <div className="h-20 w-14 rounded bg-slate-200 dark:bg-slate-800" />
                )}
                <div className="flex-1">
                  <p className="text-sm font-semibold">{comic.title}</p>
                  <p className="text-xs text-slate-500">{comic.author}</p>
                  <p className="text-xs text-slate-400">{comic.genre}</p>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <button
                  onClick={() => ctx.moveComic(comic.id, "trash", "favorite")}
                  className="flex items-center gap-2 rounded-full border border-emerald-200 px-3 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-50"
                >
                  <RotateCcw size={14} />
                  Restore
                </button>
                <button
                  onClick={() => ctx.removeFromTrash(comic.id)}
                  className="flex items-center gap-2 rounded-full border border-red-200 px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
                >
                  <Trash2 size={14} />
                  Delete
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TrashPage;
