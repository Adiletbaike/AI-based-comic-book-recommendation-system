import { useContext } from "react";
import { ComicContext } from "../../context/ComicContext";

const ComicCard = ({ comic }) => {
  const ctx = useContext(ComicContext);
  const cover = comic.coverImage || comic.cover_image;
  const isFavorite = ctx?.favorites?.some((item) => item.id === comic.id);

  return (
    <div className="flex gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#0f0f0f]">
      {cover ? (
        <img src={cover} alt={comic.title} className="h-20 w-14 rounded object-cover" />
      ) : (
        <div className="h-20 w-14 rounded bg-slate-200 dark:bg-slate-800" />
      )}
      <div className="flex-1 space-y-1">
        <h3 className="font-semibold">{comic.title}</h3>
        <p className="text-sm text-slate-600">{comic.author}</p>
        <p className="text-xs text-slate-500 dark:text-slate-400">{comic.genre}</p>
        {ctx && (
          <button
            onClick={() => ctx.addComic("favorite", comic)}
            className={`mt-2 rounded-full border px-3 py-1 text-xs font-medium ${
              isFavorite
                ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                : "border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
            }`}
            disabled={isFavorite}
          >
            {isFavorite ? "Added to Favorites" : "Add to Favorites"}
          </button>
        )}
      </div>
    </div>
  );
};

export default ComicCard;
