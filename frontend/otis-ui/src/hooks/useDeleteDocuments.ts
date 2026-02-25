import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteDocumentsFromProject, type Document } from "@/api/docApi";
import { queryKeys } from "@/api/queryKeys";

interface DeleteDocumentsParams {
    projectId: string;
    docIds: string[];
}

/**
 * useDeleteDocuments — mutation hook for deleting documents.
 *
 * On success, deleted documents are removed from the cached list
 * via `queryClient.setQueryData` for instant UI updates.
 */
export function useDeleteDocuments() {
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: ({ projectId, docIds }: DeleteDocumentsParams) =>
            deleteDocumentsFromProject(projectId, docIds),
        onSuccess: (_data, { docIds }) => {
            // Remove deleted docs from the cached list
            queryClient.setQueryData<Document[]>(
                queryKeys.documents.all,
                (old) => (old ?? []).filter((doc) => !docIds.includes(doc.doc_id)),
            );
        },
    });

    return {
        deleteDocuments: mutation.mutateAsync,
        isDeleting: mutation.isPending,
        error: mutation.error,
        reset: mutation.reset,
    };
}
