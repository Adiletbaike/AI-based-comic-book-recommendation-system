export const normalizeCoverUrl = (raw) => {
  if (!raw) return null;
  const s = String(raw).trim();
  if (!s) return null;

  // Absolute URL
  if (s.startsWith("http://") || s.startsWith("https://")) return s;

  // App-relative assets (only allow rooted paths to avoid broken relative filenames)
  if (s.startsWith("/")) return s;

  return null;
};

