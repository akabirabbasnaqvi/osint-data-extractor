import axios from "axios";
import type { JobStatusResponse, JobSummary, SearchRequest, SearchResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL: API_URL });

export async function submitSearch(payload: SearchRequest): Promise<SearchResponse> {
  const res = await client.post<SearchResponse>("/api/search", payload);
  return res.data;
}

export async function getResults(jobId: string): Promise<JobStatusResponse> {
  const res = await client.get<JobStatusResponse>(`/api/results/${jobId}`);
  return res.data;
}

export async function listJobs(): Promise<JobSummary[]> {
  const res = await client.get<JobSummary[]>("/api/jobs");
  return res.data;
}
