import apiClient from "@/lib/api/client";
import { ArtifactResponse, UploadArtifactResponse } from "@/types/artifact";

export const artifactService = {
  async upload(file: File): Promise<UploadArtifactResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiClient.post<UploadArtifactResponse>("/artifacts/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  async list(): Promise<ArtifactResponse[]> {
    const response = await apiClient.get<ArtifactResponse[]>("/artifacts");
    return response.data;
  },

  async getById(artifactId: string): Promise<ArtifactResponse> {
    const response = await apiClient.get<ArtifactResponse>(`/artifacts/${artifactId}`);
    return response.data;
  },

  async delete(artifactId: string): Promise<void> {
    await apiClient.delete(`/artifacts/${artifactId}`);
  },
};

export default artifactService;
