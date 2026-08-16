import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import artifactService from "@/services/artifactService";
import { ArtifactResponse, UploadArtifactResponse } from "@/types/artifact";

export const ARTIFACTS_QUERY_KEY = ["artifacts"];

export function useArtifacts() {
  return useQuery<ArtifactResponse[], Error>({
    queryKey: ARTIFACTS_QUERY_KEY,
    queryFn: () => artifactService.list(),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      const hasActiveProcessing = data.some(
        (artifact) => artifact.status === "pending" || artifact.status === "processing"
      );
      return hasActiveProcessing ? 3000 : false;
    },
  });
}

export function useArtifact(artifactId: string) {
  return useQuery<ArtifactResponse, Error>({
    queryKey: [...ARTIFACTS_QUERY_KEY, artifactId],
    queryFn: () => artifactService.getById(artifactId),
    enabled: Boolean(artifactId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      return data.status === "pending" || data.status === "processing" ? 3000 : false;
    },
  });
}

export function useUploadArtifact() {
  const queryClient = useQueryClient();

  return useMutation<UploadArtifactResponse, Error, File>({
    mutationFn: (file: File) => artifactService.upload(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ARTIFACTS_QUERY_KEY });
    },
  });
}

export function useDeleteArtifact() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (artifactId: string) => artifactService.delete(artifactId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ARTIFACTS_QUERY_KEY });
    },
  });
}
