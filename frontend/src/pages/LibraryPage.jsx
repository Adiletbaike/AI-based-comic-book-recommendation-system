import { useContext } from "react";
import { ComicContext } from "../context/ComicContext";

const LibraryPage = () => {
  const ctx = useContext(ComicContext);
  if (!ctx) return null;

  const columns = [
    { key: "favorite", label: "Favorites", items: ctx.favorites },
    { key: "reading", label: "In Progress", items: ctx.readingList },
    { key: "completed", label: "Completed", items: ctx.completed },
  ];

  const handleDrop = (event, toStatus) => {
    event.preventDefault();
    const raw = event.dataTransfer.getData("text/plain");
    if (!raw) return;
    try {
      const payload = JSON.parse(raw);
      if (payload?.comicId && payload?.fromStatus) {
        ctx.moveComic(payload.comicId, payload.fromStatus, toStatus);
      }
    } catch (err) {
      return;
    }
  };

  const handleDragStart = (event, comicId, fromStatus) => {
    event.dataTransfer.setData(
      "text/plain",
      JSON.stringify({ comicId, fromStatus })
    );
  };

  const renderComic = (comic, status) => {
    const cover = comic.coverImage || comic.cover_image;
    return (
      <div
        key={comic.id}
        draggable={status !== "trash"}
        onDragStart={(event) => handleDragStart(event, comic.id, status)}
        className="cursor-grab rounded-xl border border-slate-200 bg-white p-3 shadow-sm hover:border-slate-300 dark:border-slate-800 dark:bg-[#0f0f0f]"
      >
        <div className="flex gap-3">
          {cover ? (
            <img src={cover} alt={comic.title} className="h-16 w-12 rounded object-cover" />
          ) : (
            <div className="h-16 w-12 rounded bg-slate-200 dark:bg-slate-800" />
          )}
          <div className="flex-1">
            <p className="text-sm font-semibold">{comic.title}</p>
            <p className="text-xs text-slate-500">{comic.author}</p>
            <p className="text-xs text-slate-400">{comic.genre}</p>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-end gap-2">
          {status !== "trash" ? (
            <button
              onClick={() => ctx.moveComic(comic.id, status, "trash")}
              className="rounded-full border border-red-200 px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
            >
              Move to Trash
            </button>
          ) : (
            <button
              onClick={() => ctx.removeFromTrash(comic.id)}
              className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
            >
              Delete permanently
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Your Library</h1>
        <p className="text-sm text-slate-500">Manage your favorites and reading lists.</p>
      </div>

        <div className="grid gap-4 lg:grid-cols-3">
        {columns.map((column) => (
          <div
            key={column.key}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => handleDrop(event, column.key)}
            className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#171717]"
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                {column.label}
              </h2>
              <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                {column.items.length}
              </span>
            </div>

            <div className="space-y-3">
              {column.items.length === 0 && (
                <div className="rounded-lg border border-dashed border-slate-200 p-3 text-sm text-slate-400 dark:border-slate-700">
                  Drag comics here.
                </div>
              )}
              {column.items.map((comic) => renderComic(comic, column.key))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LibraryPage;
