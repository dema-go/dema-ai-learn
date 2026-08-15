import test from "node:test";
import assert from "node:assert/strict";
import {
  beginAnswerSubmission,
  createAnswerState,
  failAnswerSubmission,
  resolveAnswerSubmission,
} from "../utils/answer-state.ts";

test("starts idle and begins one submission", () => {
  const idle = createAnswerState();
  const submitting = beginAnswerSubmission(idle, 1);

  assert.deepEqual(idle, {
    phase: "idle",
    selectedIndex: -1,
    correctIndex: -1,
    isCorrect: null,
  });
  assert.equal(submitting.phase, "submitting");
  assert.equal(submitting.selectedIndex, 1);
});

test("ignores another choice while submitting", () => {
  const submitting = beginAnswerSubmission(createAnswerState(), 1);
  assert.strictEqual(beginAnswerSubmission(submitting, 2), submitting);
});

test("stores server truth for a correct answer", () => {
  const submitting = beginAnswerSubmission(createAnswerState(), 1);
  assert.deepEqual(resolveAnswerSubmission(submitting, true, 1, 1), {
    phase: "answered",
    selectedIndex: 1,
    correctIndex: 1,
    isCorrect: true,
  });
});

test("stores both wrong selection and server correct answer", () => {
  const submitting = beginAnswerSubmission(createAnswerState(), 0);
  assert.deepEqual(resolveAnswerSubmission(submitting, false, 1, 0), {
    phase: "answered",
    selectedIndex: 0,
    correctIndex: 1,
    isCorrect: false,
  });
});

test("a failed submission returns to a retryable state", () => {
  const submitting = beginAnswerSubmission(createAnswerState(), 2);
  assert.deepEqual(failAnswerSubmission(submitting), createAnswerState());
});

test("a retry resolves to the choice persisted before the lost response", () => {
  const firstSubmission = beginAnswerSubmission(createAnswerState(), 0);
  const retryable = failAnswerSubmission(firstSubmission);
  const retrySubmission = beginAnswerSubmission(retryable, 1);

  assert.deepEqual(resolveAnswerSubmission(retrySubmission, true, 0, 0), {
    phase: "answered",
    selectedIndex: 0,
    correctIndex: 0,
    isCorrect: true,
  });
});
