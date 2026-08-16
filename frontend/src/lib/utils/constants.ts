export const ALLOWED_MIME_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/jpg",
  "text/plain",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

export const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

export const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  Resume: "Resume / CV",
  Certificate: "Certificate",
  Marksheet: "Academic Marksheet",
  InternshipLetter: "Internship Letter",
  ProjectReport: "Project Report",
  Portfolio: "Portfolio",
  GitHubRepository: "GitHub Repository",
  Unknown: "Unclassified Document",
};

export const EXTRACTION_STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  SUCCESS: { bg: "bg-emerald-500/10", text: "text-emerald-500" },
  PARTIAL: { bg: "bg-amber-500/10", text: "text-amber-500" },
  FAILED: { bg: "bg-rose-500/10", text: "text-rose-500" },
  NOT_SUPPORTED: { bg: "bg-slate-500/10", text: "text-slate-400" },
  SKIPPED: { bg: "bg-slate-500/10", text: "text-slate-400" },
};
