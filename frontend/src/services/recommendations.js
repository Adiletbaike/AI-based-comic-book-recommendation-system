import { api } from "./api";

export const getChatRecommendations = async (prompt) => {
  const { data } = await api.post("/recommend/chat", { prompt });
  return data;
};

export const getPopular = async () => {
  const { data } = await api.get("/recommend/popular");
  return data;
};

export const getPersonalized = async () => {
  const { data } = await api.get("/recommend/personalized");
  return data;
};
