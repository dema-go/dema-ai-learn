export type AnswerPhase = "idle" | "submitting" | "answered";

export interface AnswerViewState {
  phase: AnswerPhase;
  selectedIndex: number;
  correctIndex: number;
  isCorrect: boolean | null;
}

export function createAnswerState(): AnswerViewState {
  return {
    phase: "idle",
    selectedIndex: -1,
    correctIndex: -1,
    isCorrect: null,
  };
}

export function beginAnswerSubmission(
  state: AnswerViewState,
  selectedIndex: number,
): AnswerViewState {
  if (state.phase !== "idle") return state;
  return { ...state, phase: "submitting", selectedIndex };
}

export function resolveAnswerSubmission(
  state: AnswerViewState,
  isCorrect: boolean,
  correctIndex: number,
): AnswerViewState {
  return { ...state, phase: "answered", isCorrect, correctIndex };
}

export function failAnswerSubmission(_state: AnswerViewState): AnswerViewState {
  return createAnswerState();
}
