import { api } from "./api";

const statusToPath = {
  favorite: "/library/favorites",
  reading: "/library/reading",
  completed: "/library/completed",
  trash: "/library/trash",
};

const statusToPost = {
  favorite: "/library/favorite",
  reading: "/library/reading",
  completed: "/library/complete",
  trash: "/library/trash",
};

export const getLibrary = async (status, query) => {
  const params = query ? { q: query } : undefined;
  const { data } = await api.get(statusToPath[status], { params });
  return data;
};

export const setStatus = async (status, comic) => {
  const { data } = await api.post(statusToPost[status], { comic });
  return data;
};

export const deleteFromTrash = async (comicId) => {
  const { data } = await api.delete(`/library/trash/${comicId}`);
  return data;
};
