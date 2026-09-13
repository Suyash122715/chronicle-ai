import apiClient from "@/lib/api/client";
import { KnowledgeGraphResponse, GraphQueryParams } from "@/types/graph";

export const graphService = {
  async getGraph(params: GraphQueryParams = {}): Promise<KnowledgeGraphResponse> {
    const searchParams: Record<string, string> = {};
    if (params.artifact_id) searchParams.artifact_id = params.artifact_id;
    if (params.entity_type) searchParams.entity_type = params.entity_type;
    if (params.include_provenance !== undefined)
      searchParams.include_provenance = String(params.include_provenance);

    const response = await apiClient.get<KnowledgeGraphResponse>("/graph", {
      params: searchParams,
    });
    return response.data;
  },
};

export default graphService;
