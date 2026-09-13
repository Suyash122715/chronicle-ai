import { useQuery } from "@tanstack/react-query";
import graphService from "@/services/graphService";
import { KnowledgeGraphResponse, GraphQueryParams } from "@/types/graph";

export const GRAPH_QUERY_KEY = ["knowledge-graph"] as const;

export function useKnowledgeGraph(params: GraphQueryParams = {}) {
  return useQuery<KnowledgeGraphResponse, Error>({
    queryKey: [...GRAPH_QUERY_KEY, params],
    queryFn: () => graphService.getGraph(params),
    staleTime: 30_000, // graph data doesn't change every second
  });
}
