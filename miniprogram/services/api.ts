const BASE = "http://127.0.0.1:8000";
const OPENID_KEY = "dev_openid";

export interface ApiError {
  error?: { code: string; message: string };
}

export function getOpenid(): string {
  let id = wx.getStorageSync(OPENID_KEY) as string;
  if (!id) {
    id = `mp-${Date.now()}`;
    wx.setStorageSync(OPENID_KEY, id);
  }
  return id;
}

export function request<T>(method: "GET" | "POST" | "DELETE", url: string, data?: object): Promise<T> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE}${url}`,
      method,
      data,
      header: {
        "Content-Type": "application/json",
        "X-Dev-Openid": getOpenid(),
      },
      success(res) {
        const status = res.statusCode || 0;
        if (status >= 200 && status < 300) {
          resolve(res.data as T);
          return;
        }
        reject(res.data);
      },
      fail(err) {
        reject({ error: { code: "NETWORK", message: err.errMsg || "网络不可用" } });
      },
    });
  });
}

export function errorMessage(err: unknown, fallback: string): string {
  const body = err as ApiError;
  return body?.error?.message || fallback;
}

export const api = {
  home: () => request<HomeResponse>("GET", "/api/home"),
  me: () => request<MeStats>("GET", "/api/me"),
  generate: (payload: GenerateRequest) => request<GenerateResponse>("POST", "/api/quiz/generate", payload),
  task: (taskId: string) => request<TaskResponse>("GET", `/api/quiz/task/${taskId}`),
  quiz: (quizId: string) => request<QuizResponse>("GET", `/api/quiz/${quizId}`),
  answer: (quizId: string, payload: AnswerRequest) =>
    request<AnswerResponse>("POST", `/api/quiz/${quizId}/answer`, payload),
  retest: (quizId: string) => request<GenerateResponse>("POST", `/api/quiz/${quizId}/retest`),
  recent: (filter = "all") => request<{ items: RecentItem[] }>("GET", `/api/quiz/recent?filter=${filter}`),
  feedback: (questionId: string, errorType: string) =>
    request<{ ok: boolean }>("POST", `/api/question/${questionId}/feedback`, { error_type: errorType }),
  deleteMaterial: (materialId: string) => request<{ ok: boolean }>("DELETE", `/api/material/${materialId}`),
  track: (name: string, payload: object = {}) => request<{ ok: boolean }>("POST", "/api/events", { name, payload }),
};

export interface Quota {
  used: number;
  limit: number;
  reset_at: string;
}

export interface PrimaryTask {
  type: "retest" | "continue" | "create";
  quiz_id?: string;
  material_id?: string;
  title?: string;
  wrong_count?: number;
  current_ordinal?: number;
  question_count?: number;
}

export interface RecentItem {
  quiz_id: string;
  material_id: string;
  title: string;
  status: "active" | "completed" | "retest";
  correct?: number;
  total?: number;
  wrong_count?: number;
  current_ordinal?: number;
  created_at: string;
}

export interface MeStats {
  streak_days: number;
  stars: number;
  completed_count: number;
  retest_count?: number;
}

export interface HomeResponse {
  quota: Quota;
  primary_task: PrimaryTask;
  recent: RecentItem[];
  me: MeStats;
}

export interface GenerateRequest {
  source_type: "text" | "url";
  text?: string;
  url?: string;
  channel?: string;
}

export interface GenerateResponse {
  task_id: string;
  status: string;
  quiz_id?: string;
}

export interface TaskResponse {
  task_id: string;
  status: string;
  progress: string;
  stage: string;
  quiz_id?: string;
  question_count?: number;
  error?: string;
}

export interface Question {
  question_id: string;
  question_type: "single" | "true_false";
  stem: string;
  options: string[];
  answer_index: number;
  explanation: string;
  source_span: string;
  quality_status: string;
  knowledge_point?: string;
  ordinal?: number;
}

export interface QuizResponse {
  id: string;
  material_id: string;
  title: string;
  question_count: number;
  is_degraded: boolean;
  is_retest: boolean;
  parent_quiz_id?: string;
  questions: Question[];
  ai_notice: string;
}

export interface AnswerRequest {
  question_id: string;
  chosen_index: number;
  attempt_id?: string;
}

export interface AnswerResponse {
  is_correct: boolean;
  correct_index: number;
  explanation: string;
  source_span: string;
  attempt_id: string;
  next_question_id?: string;
  finished: boolean;
  result?: {
    correct: number;
    total: number;
    duration_seconds: number;
    wrong_question_ids: string[];
  };
}
