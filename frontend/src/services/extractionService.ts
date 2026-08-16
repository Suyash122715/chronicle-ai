import apiClient from "@/lib/api/client";
import { ExtractionResponse } from "@/types/extraction";

export const extractionService = {
  async getByArtifactId(artifactId: string): Promise<ExtractionResponse> {
    const response = await apiClient.get<ExtractionResponse>(`/artifacts/${artifactId}/extraction`);
    return response.data;
  },
};

export default extractionService;
