// Mirrors backend/schemas/search_request.py and result_response.py.
// Kept as one source of truth on the frontend so the form and results
// page can't silently drift out of sync with each other.

export interface SearchInputs {
  full_name?: string;
  email?: string;
  linkedin?: string;
  facebook?: string;
  instagram?: string;
  company_name?: string;
  company_website?: string;
  personal_email?: string;
  city?: string;
  country?: string;
  github?: string;
  twitter?: string;
}

export type OutputCategory =
  | "personal_email"
  | "work_email"
  | "phone"
  | "linkedin"
  | "github"
  | "twitter"
  | "facebook"
  | "instagram"
  | "personal_website"
  | "company";

export interface SearchRequest {
  inputs: SearchInputs;
  retrieve: OutputCategory[];
}

export interface SearchResponse {
  job_id: string;
  status: JobStatus;
}

export type JobStatus = "pending" | "running" | "completed" | "failed";

export interface ResultEntry {
  data: Record<string, unknown>;
  source_url: string | null;
  confidence: number;
  scraped_at: string;
}

export interface JobSummary {
  job_id: string;
  status: JobStatus;
  progress: number;
  created_at: string;
  inputs: SearchInputs;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  created_at: string;
  completed_at: string | null;
  error_msg: string | null;
  results: Partial<Record<OutputCategory, ResultEntry[]>>;
}
