import { useState, useEffect, useRef } from "react";
import api from "@/api/authApi";

// Global cache for thumbnails to prevent re-fetching
const thumbnailCache = new Map<string, string>();

export function useThumbnail(docId: string) {
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(() => {
    // Check cache on initial render
    return thumbnailCache.get(docId) || null;
  });
  const [isLoading, setIsLoading] = useState(() => !thumbnailCache.has(docId));
  const [error, setError] = useState<Error | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;

    // If already cached, use the cached value
    if (thumbnailCache.has(docId)) {
      setThumbnailUrl(thumbnailCache.get(docId)!);
      setIsLoading(false);
      return;
    }

    const fetchThumbnail = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.get(`/v1/documents/${docId}/thumbnail`, {
          responseType: "blob",
        });

        // Create an object URL from the blob
        const objectUrl = URL.createObjectURL(response.data);

        // Store in cache
        thumbnailCache.set(docId, objectUrl);

        if (isMounted.current) {
          setThumbnailUrl(objectUrl);
        }
      } catch (err) {
        if (isMounted.current) {
          setError(err as Error);
          setThumbnailUrl(null);
        }
      } finally {
        if (isMounted.current) {
          setIsLoading(false);
        }
      }
    };

    fetchThumbnail();

    return () => {
      isMounted.current = false;
    };
  }, [docId]);

  return { thumbnailUrl, isLoading, error };
}

// Optional: Clear cache for a specific docId (useful when document is updated)
export function clearThumbnailCache(docId?: string) {
  if (docId) {
    const url = thumbnailCache.get(docId);
    if (url) {
      URL.revokeObjectURL(url);
      thumbnailCache.delete(docId);
    }
  } else {
    // Clear all
    thumbnailCache.forEach((url) => URL.revokeObjectURL(url));
    thumbnailCache.clear();
  }
}
