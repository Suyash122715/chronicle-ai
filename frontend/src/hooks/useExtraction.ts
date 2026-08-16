import { useQuery } from "@tanstack/react-query";
import extractionService from "@/services/extractionService";
import { ExtractionResponse } from "@/types/extraction";
import { ApiError } from "@/types/api";

export const EXTRACTIONS_QUERY_KEY = ["extractions"];

export function useExtraction(artifactId: string, enabled: boolean = true) {
  return useQuery<ExtractionResponse, ApiError>({
    queryKey: [...EXTRACTIONS_QUERY_KEY, artifactId],
    queryFn: () => extractionService.getByArtifactId(artifactId),
    enabled: Boolean(artifactId) && enabled,
    retry: (failureCount, error) => {
      // Do not retry if extraction is 404 (not generated yet)
      if (error?.status === 404) return false;
      return failureCount < 2;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
