import { useContext } from "react";
import { ComicContext } from "../../context/ComicContext";
import RecommendationDisplay from "../Home/RecommendationDisplay";

const Favorites = () => {
  const ctx = useContext(ComicContext);
  if (!ctx) return null;
  return <RecommendationDisplay comics={ctx.favorites} />;
};

export default Favorites;
