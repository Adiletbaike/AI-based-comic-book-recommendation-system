import ComicCard from "./ComicCard";

const RecommendationDisplay = ({ comics }) => {
  if (!comics.length) {
    return <p className="text-sm text-slate-500">No recommendations yet.</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      {comics.map((comic) => (
        <ComicCard key={comic.id} comic={comic} />
      ))}
    </div>
  );
};

export default RecommendationDisplay;
