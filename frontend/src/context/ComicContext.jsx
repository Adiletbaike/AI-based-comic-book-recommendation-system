import React, { createContext, useEffect, useMemo, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { deleteFromTrash, getLibrary, setStatus } from "../services/library";

export const ComicContext = createContext(undefined);

export const ComicProvider = ({ children }) => {
  const { token, isReady } = useAuth();
  const [favorites, setFavorites] = useState([]);
  const [readingList, setReadingList] = useState([]);
  const [completed, setCompleted] = useState([]);
  const [trash, setTrash] = useState([]);

  const ensureUnique = (items) => {
    const map = new Map();
    items.forEach((item) => {
      if (item && item.id != null) map.set(item.id, item);
    });
    return Array.from(map.values());
  };

  const setLibrary = (status, comics) => {
    if (status === "favorite") setFavorites(comics);
    if (status === "reading") setReadingList(comics);
    if (status === "completed") setCompleted(comics);
    if (status === "trash") setTrash(comics);
  };

  useEffect(() => {
    if (!isReady) return;
    if (!token) {
      setFavorites([]);
      setReadingList([]);
      setCompleted([]);
      setTrash([]);
      return;
    }
    const load = async () => {
      try {
        const [fav, reading, done, trashItems] = await Promise.all([
          getLibrary("favorite"),
          getLibrary("reading"),
          getLibrary("completed"),
          getLibrary("trash"),
        ]);
        setFavorites(fav || []);
        setReadingList(reading || []);
        setCompleted(done || []);
        setTrash(trashItems || []);
      } catch (err) {
        return;
      }
    };
    load();
  }, [token, isReady]);

  const addComic = (status, comic) => {
    if (!comic || comic.id == null) return;
    if (status === "favorite") setFavorites((prev) => ensureUnique([comic, ...prev]));
    if (status === "reading") setReadingList((prev) => ensureUnique([comic, ...prev]));
    if (status === "completed") setCompleted((prev) => ensureUnique([comic, ...prev]));
    if (status === "trash") setTrash((prev) => ensureUnique([comic, ...prev]));
    if (token) {
      setStatus(status, comic).catch(() => {});
    }
  };

  const moveComic = (comicId, fromStatus, toStatus) => {
    if (!comicId || fromStatus === toStatus) return;
    const pull = (list) => list.filter((item) => item.id !== comicId);
    const find = (list) => list.find((item) => item.id === comicId);

    let moving = null;
    if (fromStatus === "favorite") moving = find(favorites);
    if (fromStatus === "reading") moving = find(readingList);
    if (fromStatus === "completed") moving = find(completed);
    if (fromStatus === "trash") moving = find(trash);
    if (!moving) return;

    if (fromStatus === "favorite") setFavorites((prev) => pull(prev));
    if (fromStatus === "reading") setReadingList((prev) => pull(prev));
    if (fromStatus === "completed") setCompleted((prev) => pull(prev));
    if (fromStatus === "trash") setTrash((prev) => pull(prev));

    addComic(toStatus, moving);
  };

  const removeFromTrash = (comicId) => {
    if (!comicId) return;
    setTrash((prev) => prev.filter((item) => item.id !== comicId));
    if (token) {
      deleteFromTrash(comicId).catch(() => {});
    }
  };

  const value = useMemo(
    () => ({
      favorites,
      readingList,
      completed,
      trash,
      setLibrary,
      addComic,
      moveComic,
      removeFromTrash,
    }),
    [favorites, readingList, completed, trash]
  );

  return <ComicContext.Provider value={value}>{children}</ComicContext.Provider>;
};
