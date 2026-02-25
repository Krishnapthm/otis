import { useQuery } from "@tanstack/react-query";
import { getAllUserDocuments, type Document } from "@/api/docApi";
import { queryKeys } from "@/api/queryKeys";

/**
 * useDocuments — cached query for the user's document library.
 *
 * Documents are fetched once and cached for 5 minutes (staleTime).
 * Every component that calls this hook shares the same cache entry,
 * so the mention dropdown, data library, and attachment UI all read
 * from a single source of truth without redundant network requests.
 */
export function useDocuments() {
    const query = useQuery<Document[]>({
        queryKey: queryKeys.documents.all,
        queryFn: getAllUserDocuments,
        staleTime: 5 * 60 * 1000, // 5 minutes — documents rarely change
        gcTime: 10 * 60 * 1000, // 10 minutes — keep in garbage-collectable cache
    });

    return {
        documents: query.data ?? [],
        isLoading: query.isLoading,
        isError: query.isError,
        error: query.error,
        refetch: query.refetch,
    };
}
