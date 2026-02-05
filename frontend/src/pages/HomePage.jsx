import { useState } from "react";
import ChatInterface from "../components/Home/ChatInterface";
import RecommendationDisplay from "../components/Home/RecommendationDisplay";

const HomePage = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [lastPrompt, setLastPrompt] = useState("");
  const [lastExplanation, setLastExplanation] = useState("");

  const handleRecommendations = ({ recommendations, explanation, prompt }) => {
    setRecommendations(recommendations);
    setLastPrompt(prompt);
    setLastExplanation(explanation);
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-[#171717]">
        <h1 className="text-2xl font-semibold">AI Comic Recommendations</h1>
        <p className="mt-2 text-sm text-slate-500">
          Chat with the assistant to get tailored comic picks.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <ChatInterface onRecommendations={handleRecommendations} />

        <aside className="h-full rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-[#171717]">
          <div className="mb-4">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Recommendations
            </h2>
            {lastPrompt && (
              <p className="mt-2 text-xs text-slate-500">
                Based on: <span className="font-medium text-slate-700">{lastPrompt}</span>
              </p>
            )}
            {lastExplanation && (
              <p className="mt-2 text-xs text-slate-500">{lastExplanation}</p>
            )}
          </div>

          <RecommendationDisplay comics={recommendations} />
        </aside>
      </div>
    </div>
  );
};

export default HomePage;
