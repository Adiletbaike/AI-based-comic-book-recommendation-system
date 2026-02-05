import { useContext } from "react";
import { ComicContext } from "../../context/ComicContext";
import RecommendationDisplay from "../Home/RecommendationDisplay";

const Completed = () => {
  const ctx = useContext(ComicContext);
  if (!ctx) return null;
  return <RecommendationDisplay comics={ctx.completed} />;
};

export default Completed;
