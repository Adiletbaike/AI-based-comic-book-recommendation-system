import { useContext } from "react";
import { ComicContext } from "../../context/ComicContext";
import RecommendationDisplay from "../Home/RecommendationDisplay";

const ReadingList = () => {
  const ctx = useContext(ComicContext);
  if (!ctx) return null;
  return <RecommendationDisplay comics={ctx.readingList} />;
};

export default ReadingList;
