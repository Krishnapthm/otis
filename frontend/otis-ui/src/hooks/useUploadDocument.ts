import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadUserDocuments, type Document } from "@/api/docApi";
import { queryKeys } from "@/api/queryKeys";

/**
 * useUploadDocument — mutation hook for uploading documents.
 *
 * On success, newly uploaded documents are prepended to the cached
 * document list via `queryClient.setQueryData`, so every consumer
 * (data library, mention dropdown, attachment UI) sees the new
 * documents instantly without a refetch.
 */
export function useUploadDocument() {
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: (files: File[]) => uploadUserDocuments(files),
        onSuccess: (uploadedDocs: Document[]) => {
            // Optimistically prepend new docs to the cached list
            queryClient.setQueryData<Document[]>(
                queryKeys.documents.all,
                (old) => [...uploadedDocs, ...(old ?? [])],
            );
        },
    });

    return {
        uploadDocuments: mutation.mutateAsync,
        isUploading: mutation.isPending,
        error: mutation.error,
        reset: mutation.reset,
    };
}
