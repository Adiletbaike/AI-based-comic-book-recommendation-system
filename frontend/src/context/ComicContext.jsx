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

  const stableKey = (item) => {
    if (!item) return null;
    if (item.id != null) return `id:${String(item.id)}`;
    return `ta:${String(item.title || "")}|${String(item.author || "")}`;
  };

  const ensureUnique = (items) => {
    const map = new Map();
    items.forEach((item) => {
      const key = stableKey(item);
      if (key) map.set(key, item);
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

  const addComic = async (status, comic) => {
    if (!comic) return;

    // If authenticated, persist first and then store the server's canonical comic (numeric DB id).
    if (token) {
      try {
        const resp = await setStatus(status, comic);
        const serverComic = resp?.comic;
        if (!serverComic) return;

        if (status === "favorite") setFavorites((prev) => ensureUnique([serverComic, ...prev]));
        if (status === "reading") setReadingList((prev) => ensureUnique([serverComic, ...prev]));
        if (status === "completed") setCompleted((prev) => ensureUnique([serverComic, ...prev]));
        if (status === "trash") setTrash((prev) => ensureUnique([serverComic, ...prev]));
        return;
      } catch (err) {
        return;
      }
    }

    // Unauthenticated: local-only library.
    if (status === "favorite") setFavorites((prev) => ensureUnique([comic, ...prev]));
    if (status === "reading") setReadingList((prev) => ensureUnique([comic, ...prev]));
    if (status === "completed") setCompleted((prev) => ensureUnique([comic, ...prev]));
    if (status === "trash") setTrash((prev) => ensureUnique([comic, ...prev]));
  };

  const moveComic = async (comicId, fromStatus, toStatus) => {
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

    await addComic(toStatus, moving);
  };

  const removeFromTrash = async (comicId) => {
    if (!comicId) return;
    if (token) {
      try {
        await deleteFromTrash(comicId);
        setTrash((prev) => prev.filter((item) => item.id !== comicId));
      } catch (err) {
        return;
      }
      return;
    }
    setTrash((prev) => prev.filter((item) => item.id !== comicId));
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
