# Quiz UI Spacing and Immediate Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make quiz choices nearly full-width, submit an answer immediately on tap, render correct and wrong states directly on choices, keep the next action visible, and apply consistent spacing to buttons across the existing mini program.

**Architecture:** Add a small pure TypeScript answer-state module and test it with Node's built-in test runner, then let the existing quiz page own API calls and render the state returned by the backend. Keep quiz-only layout in `pages/quiz/quiz.wxss`, keep reusable spacing rules in `app.wxss`, and add Python contract tests for WXML/WXSS/controller wiring because the repository does not yet have WeChat component automation.

**Tech Stack:** WeChat native mini program, TypeScript, WXML, WXSS, Node.js 25 built-in test runner, Python `unittest`, existing FastAPI contract tests.

## Global Constraints

- Work only in `/Users/liuziying/Projects/dema-ai-learn/.worktrees/ui-spacing-redesign` on branch `codex/ui-spacing-redesign`.
- The page horizontal safe margin is exactly `16px`.
- Quiz choices use the full width inside that safe margin and have a minimum height of exactly `56px`.
- Choice-to-choice and same-group button spacing is exactly `12px`.
- Primary-to-secondary action-group spacing is `16–20px`; use `20px` in the shared implementation.
- Tapping a choice submits immediately; there is no “确定答案” action.
- The UI must use the answer API response fields `is_correct` and `correct_index`; it must not judge correctness from `question.answer_index`.
- A wrong answer shows a red cross on the selected choice and a green check plus “正确答案” on the correct choice.
- Explanation and source entry appear below the complete choice group; the bottom next action remains fixed above the WeChat safe area.
- During submission, choices are locked; after failure, no answer is revealed and choices become retryable.
- Correct and wrong states must use icon, text, border, and color together.
- Preserve strict source attribution, the AI-generated notice, question reporting, result persistence, and the existing backend API contract.
- Do not add a component library, new product capability, new question type, or new backend field.
- Unit tests must use fixtures and local code only; they must not call DeepSeek or any production service.

---

## File Structure

- Create `miniprogram/utils/answer-state.ts`: pure answer-view state and transitions with no `wx` dependency.
- Create `miniprogram/tests/answer-state.test.mjs`: executable unit tests for immediate submission, duplicate-tap protection, success, and failure reset.
- Modify `miniprogram/package.json`: expose the local Node test command without adding dependencies.
- Modify `backend/tests/test_quiz_api.py`: require safe replay of an answer after a lost response.
- Modify `backend/app/services/attempts.py`: return the stored server result for an already-recorded question without scoring twice.
- Create `tests/test_miniprogram_ui.py`: repository-level WXML/WXSS/controller contract tests.
- Modify `miniprogram/pages/quiz/quiz.ts`: call the answer API from option taps and drive the pure state transitions.
- Modify `miniprogram/pages/quiz/quiz.wxml`: remove duplicate metadata and confirmation, render inline state, explanation, source, and fixed action.
- Modify `miniprogram/pages/quiz/quiz.wxss`: own quiz-specific full-width choice and fixed-bottom layout.
- Modify `miniprogram/app.wxss`: own reusable page margins, button gaps, card gaps, and action-group spacing.
- Modify `miniprogram/pages/result/result.wxml`: prevent duplicate “再考一篇” in the no-wrong-answer state.
- Modify `TODO.md`: close the recorded UI spacing item after verification and associate it with the implementation commit.

---

### Task 1: Add a Pure Answer-State Model

**Files:**
- Create: `miniprogram/utils/answer-state.ts`
- Create: `miniprogram/tests/answer-state.test.mjs`
- Modify: `miniprogram/package.json`

**Interfaces:**
- Consumes: answer API response values `is_correct: boolean` and `correct_index: number`.
- Produces: `AnswerViewState`, `createAnswerState()`, `beginAnswerSubmission()`, `resolveAnswerSubmission()`, and `failAnswerSubmission()` for the quiz page.

- [ ] **Step 1: Add the failing state-transition tests**

Create `miniprogram/tests/answer-state.test.mjs`:

```javascript
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
  assert.deepEqual(resolveAnswerSubmission(submitting, true, 1), {
    phase: "answered",
    selectedIndex: 1,
    correctIndex: 1,
    isCorrect: true,
  });
});

test("stores both wrong selection and server correct answer", () => {
  const submitting = beginAnswerSubmission(createAnswerState(), 0);
  assert.deepEqual(resolveAnswerSubmission(submitting, false, 1), {
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
```

Modify `miniprogram/package.json` to add the script while preserving the existing dependency:

```json
"scripts": {
  "test": "node --test tests/*.test.mjs"
}
```

- [ ] **Step 2: Run the tests and verify the missing module failure**

Run:

```bash
cd miniprogram
npm test
```

Expected: FAIL with `ERR_MODULE_NOT_FOUND` for `utils/answer-state.ts`.

- [ ] **Step 3: Implement the minimal pure state model**

Create `miniprogram/utils/answer-state.ts`:

```typescript
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
```

- [ ] **Step 4: Run the unit tests and verify they pass**

Run:

```bash
cd miniprogram
npm test
```

Expected: 5 tests PASS and 0 tests FAIL.

- [ ] **Step 5: Commit the state model**

```bash
git add miniprogram/package.json miniprogram/tests/answer-state.test.mjs miniprogram/utils/answer-state.ts
git commit -m "test: add quiz answer state model"
```

---

### Task 2: Make Answer Submission Safe to Retry

**Files:**
- Modify: `backend/tests/test_quiz_api.py`
- Modify: `backend/app/services/attempts.py`

**Interfaces:**
- Consumes: the existing `POST /api/quiz/{quiz_id}/answer` request and response fields.
- Produces: idempotent replay for an answer already stored under the same user, quiz, attempt, and question; no new request or response field.

- [ ] **Step 1: Replace the duplicate-rejection test with a failing replay test**

Replace `test_duplicate_answer_rejected` in `backend/tests/test_quiz_api.py` with:

```python
def test_duplicate_answer_returns_stored_result_without_scoring_twice(client):
    quiz = ready_quiz(client)
    first = quiz["questions"][0]
    payload = {
        "question_id": first["question_id"],
        "chosen_index": first["answer_index"],
    }

    first_res = client.post(f"/api/quiz/{quiz['id']}/answer", json=payload)
    assert first_res.status_code == 200
    first_body = first_res.json()

    replay = client.post(
        f"/api/quiz/{quiz['id']}/answer",
        json={**payload, "chosen_index": (first["answer_index"] + 1) % len(first["options"])},
    )
    assert replay.status_code == 200
    replay_body = replay.json()
    assert replay_body["attempt_id"] == first_body["attempt_id"]
    assert replay_body["is_correct"] is True
    assert replay_body["correct_index"] == first["answer_index"]

    last = None
    for question in quiz["questions"][1:]:
        last = client.post(
            f"/api/quiz/{quiz['id']}/answer",
            json={
                "attempt_id": first_body["attempt_id"],
                "question_id": question["question_id"],
                "chosen_index": question["answer_index"],
            },
        )
    assert last is not None
    assert last.json()["result"]["correct"] == len(quiz["questions"])

    last_question = quiz["questions"][-1]
    completed_replay = client.post(
        f"/api/quiz/{quiz['id']}/answer",
        json={
            "question_id": last_question["question_id"],
            "chosen_index": last_question["answer_index"],
        },
    )
    assert completed_replay.status_code == 200
    assert completed_replay.json()["result"]["correct"] == len(quiz["questions"])
```

The second request deliberately carries a different choice. The server must return the first stored result rather than overwrite the answer or increment the score. The final replay omits `attempt_id` to cover a lost response on the last question after the attempt is already complete.

- [ ] **Step 2: Run the focused backend test and verify it fails**

Run:

```bash
cd backend
pytest tests/test_quiz_api.py::test_duplicate_answer_returns_stored_result_without_scoring_twice -q
```

Expected: FAIL because the replay currently returns HTTP 409 `ALREADY_ANSWERED`.

- [ ] **Step 3: Extract one response builder for new and replayed answers**

Add this helper above `submit_answer()` in `backend/app/services/attempts.py`:

```python
def _answer_response(
    db: Session,
    quiz: Quiz,
    question: Question,
    attempt: Attempt,
    answer: Answer,
) -> dict:
    answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    finished = len(answers) >= quiz.question_count
    result = None
    next_question_id = None
    if finished:
        wrong_ids = [item.question_id for item in answers if not item.is_correct]
        result = {
            "correct": attempt.score,
            "total": quiz.question_count,
            "duration_seconds": _duration_seconds(attempt.started_at, attempt.completed_at),
            "wrong_question_ids": wrong_ids,
        }
    else:
        answered_ids = {item.question_id for item in answers}
        remaining = [
            item
            for item in sorted(quiz.questions, key=lambda row: row.ordinal)
            if item.id not in answered_ids
        ]
        if remaining:
            next_question_id = remaining[0].id
    return {
        "is_correct": answer.is_correct,
        "correct_index": question.answer_index,
        "explanation": question.explanation,
        "source_span": question.source_span,
        "attempt_id": attempt.id,
        "next_question_id": next_question_id,
        "finished": finished,
        "result": result,
    }
```

- [ ] **Step 4: Return stored truth for a replay without mutating score**

In the branch where the request has no `attempt_id`, look for a just-completed answer before creating a new attempt:

```python
else:
    attempt = get_open_attempt(db, quiz, user.id)
    if attempt is None:
        latest = get_latest_attempt(db, quiz, user.id)
        if latest is not None:
            replayed = (
                db.query(Answer)
                .filter(Answer.attempt_id == latest.id, Answer.question_id == question.id)
                .one_or_none()
            )
            if replayed is not None:
                return _answer_response(db, quiz, question, latest, replayed)
    if attempt is None:
        attempt = Attempt(quiz_id=quiz.id, user_id=user.id, current_ordinal=question.ordinal)
        db.add(attempt)
        db.flush()
```

Replace the current `ALREADY_ANSWERED` exception with:

```python
if existing is not None:
    return _answer_response(db, quiz, question, attempt, existing)
```

For the new-answer path, bind the row to a local variable before adding it:

```python
answer = Answer(
    attempt_id=attempt.id,
    question_id=question.id,
    chosen_index=chosen_index,
    is_correct=is_correct,
)
db.add(answer)
```

Keep the existing first-answer event, score increment, star increment, ordinal update, completion timestamp, and completion event. Replace only the duplicated response-building block at the end with:

```python
answered_count = db.query(Answer).filter(Answer.attempt_id == attempt.id).count()
if answered_count >= quiz.question_count:
    attempt.completed_at = utcnow()
    if not quiz.is_retest:
        user.streak_days = max(user.streak_days, 1)
    track_event(
        db,
        user.id,
        "quiz_completed",
        {"quiz_id": quiz.id, "score": attempt.score},
    )
db.flush()
return _answer_response(db, quiz, question, attempt, answer)
```

Delete the old local `answers`, `finished`, `result`, `next_question_id`, wrong-ID, remaining-question, and response-dictionary block because `_answer_response()` now owns those read-only calculations.

- [ ] **Step 5: Run the focused and full backend tests**

Run:

```bash
cd backend
pytest tests/test_quiz_api.py -q
pytest tests/ -q
```

Expected: all tests PASS; replay returns the original stored result and the final score never exceeds the question count.

- [ ] **Step 6: Commit the retry-safe answer endpoint**

```bash
git add backend/tests/test_quiz_api.py backend/app/services/attempts.py
git commit -m "fix: make quiz answer replay idempotent"
```

---

### Task 3: Submit Immediately From the Quiz Page

**Files:**
- Create: `tests/test_miniprogram_ui.py`
- Modify: `miniprogram/pages/quiz/quiz.ts`
- Modify: `miniprogram/pages/quiz/quiz.wxml`

**Interfaces:**
- Consumes: Task 1 state functions and the existing `api.answer(quizId, AnswerRequest): Promise<AnswerResponse>`.
- Produces: `onSelect()` as the only answer-submission entry point and `onNext()` as navigation after a resolved answer.

- [ ] **Step 1: Add failing controller and markup contract tests**

Create `tests/test_miniprogram_ui.py`:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MINIPROGRAM = ROOT / "miniprogram"


class MiniProgramQuizUiContractTests(unittest.TestCase):
    def setUp(self):
        self.quiz_ts = (MINIPROGRAM / "pages/quiz/quiz.ts").read_text(encoding="utf-8")
        self.quiz_wxml = (MINIPROGRAM / "pages/quiz/quiz.wxml").read_text(encoding="utf-8")

    def test_choice_tap_submits_and_confirmation_is_removed(self):
        self.assertIn("async onSelect", self.quiz_ts)
        self.assertIn("beginAnswerSubmission", self.quiz_ts)
        self.assertIn("await api.answer", self.quiz_ts)
        self.assertIn("resolveAnswerSubmission", self.quiz_ts)
        self.assertIn("failAnswerSubmission", self.quiz_ts)
        self.assertNotIn("async onConfirm", self.quiz_ts)
        self.assertNotIn("确定答案", self.quiz_wxml)
        self.assertIn('bindtap="onNext"', self.quiz_wxml)

    def test_markup_uses_server_correct_index_and_explicit_marks(self):
        self.assertIn("answer.correctIndex", self.quiz_wxml)
        self.assertNotIn("question.answer_index", self.quiz_wxml)
        self.assertIn("✓", self.quiz_wxml)
        self.assertIn("×", self.quiz_wxml)
        self.assertIn("正确答案", self.quiz_wxml)
        self.assertIn("回答正确", self.quiz_wxml)
        self.assertIn("这次选错了", self.quiz_wxml)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_miniprogram_ui.MiniProgramQuizUiContractTests -v
```

Expected: FAIL because `onSelect` is synchronous, `onConfirm` and “确定答案” still exist, and WXML still uses `question.answer_index`.

- [ ] **Step 3: Wire immediate submission in `quiz.ts`**

Import the Task 1 module:

```typescript
import {
  AnswerViewState,
  beginAnswerSubmission,
  createAnswerState,
  failAnswerSubmission,
  resolveAnswerSubmission,
} from "../../utils/answer-state";
```

Replace `selected`, `submitted`, and `isCorrect` in page data with:

```typescript
answer: createAnswerState() as AnswerViewState,
```

Replace `onSelect` and the submission half of `onConfirm` with:

```typescript
async onSelect(event: WechatMiniprogram.TouchEvent) {
  const selectedIndex = Number(event.currentTarget.dataset.index);
  const submitting = beginAnswerSubmission(this.data.answer, selectedIndex);
  if (submitting === this.data.answer) return;

  this.setData({ answer: submitting });
  try {
    const question = this.data.question as Question;
    const res = await api.answer(this.data.quiz.id, {
      question_id: question.question_id,
      chosen_index: selectedIndex,
      attempt_id: this.data.attemptId || undefined,
    });
    this.setData({
      answer: resolveAnswerSubmission(submitting, res.is_correct, res.correct_index),
      explanation: res.explanation,
      sourceSpan: res.source_span,
      showSource: false,
      finished: res.finished,
      attemptId: res.attempt_id,
    });
    if (res.result) {
      wx.setStorageSync("last_result", {
        quizId: this.data.quiz.id,
        title: this.data.quiz.title,
        ...res.result,
      });
    }
  } catch (err) {
    this.setData({ answer: failAnswerSubmission(submitting) });
    wx.showToast({ title: errorMessage(err, "提交失败，请重新选择"), icon: "none" });
  }
},
```

Rename the navigation half to `onNext()`. Guard it with `if (this.data.answer.phase !== "answered") return;`, preserve result redirection, and reset each next question with `answer: createAnswerState()` plus the existing explanation/source/progress resets.

- [ ] **Step 4: Replace quiz markup with server-backed option states**

Keep one metadata row, one progress bar, and one question-type label. Wrap choices in `<view class="choice-list">` and use this class expression:

```xml
class="choice-card {{answer.phase === 'submitting' && answer.selectedIndex === optIndex ? 'submitting' : ''}} {{answer.phase === 'answered' && answer.correctIndex === optIndex ? 'correct' : ''}} {{answer.phase === 'answered' && answer.selectedIndex === optIndex && answer.selectedIndex !== answer.correctIndex ? 'wrong' : ''}}"
```

Lock options outside idle state:

```xml
disabled="{{answer.phase !== 'idle'}}"
```

Render a stable leading mark and the correct-answer label:

```xml
<text class="choice-key" wx:if="{{answer.phase === 'answered' && answer.correctIndex === optIndex}}">✓</text>
<text class="choice-key" wx:elif="{{answer.phase === 'answered' && answer.selectedIndex === optIndex}}">×</text>
<text class="choice-key" wx:else>{{keys[optIndex]}}</text>
<text class="choice-copy">{{item}}</text>
<text class="correct-label" wx:if="{{answer.phase === 'answered' && answer.correctIndex === optIndex && !answer.isCorrect}}">正确答案</text>
```

Replace the old feedback card with:

```xml
<view class="answer-feedback" wx:if="{{answer.phase === 'answered'}}">
  <view class="feedback-title">{{answer.isCorrect ? '✓ 回答正确' : '× 这次选错了'}}</view>
  <view class="feedback-copy">{{explanation}}</view>
</view>
<button class="source-toggle" wx:if="{{answer.phase === 'answered'}}" bindtap="toggleSource">🔎 {{showSource ? '收起原文依据' : '查看原文依据'}}</button>
```

Keep the source drawer and AI notice, then add the fixed action markup:

```xml
<view class="bottom-action">
  <view class="bottom-hint" wx:if="{{answer.phase !== 'answered'}}">
    {{answer.phase === 'submitting' ? '正在提交答案…' : '点选答案后立即判题'}}
  </view>
  <button class="btn" wx:else bindtap="onNext">{{finished ? '查看结果' : '下一题'}}</button>
</view>
```

- [ ] **Step 5: Run the state and contract tests**

Run:

```bash
cd miniprogram && npm test
cd .. && python3 -m unittest tests.test_miniprogram_ui.MiniProgramQuizUiContractTests -v
```

Expected: all Node and Python tests PASS.

- [ ] **Step 6: Commit the immediate-submit behavior**

```bash
git add tests/test_miniprogram_ui.py miniprogram/pages/quiz/quiz.ts miniprogram/pages/quiz/quiz.wxml
git commit -m "feat: submit quiz answers on choice tap"
```

---

### Task 4: Implement Full-Width Choices and the Fixed Bottom Action

**Files:**
- Modify: `tests/test_miniprogram_ui.py`
- Modify: `miniprogram/pages/quiz/quiz.wxml`
- Modify: `miniprogram/pages/quiz/quiz.wxss`
- Modify: `miniprogram/app.wxss`

**Interfaces:**
- Consumes: Task 3 WXML class names and `AnswerViewState` phases.
- Produces: page-local choice, feedback, source, loading, and safe-area bottom-action styles.

- [ ] **Step 1: Add failing layout contract tests**

Extend `setUp()` in `tests/test_miniprogram_ui.py`:

```python
self.quiz_wxss = (MINIPROGRAM / "pages/quiz/quiz.wxss").read_text(encoding="utf-8")
```

Add:

```python
def test_quiz_layout_uses_full_width_choices_and_fixed_action(self):
    compact = "".join(self.quiz_wxss.split())
    self.assertIn(".quiz-screen{padding-left:16px;padding-right:16px", compact)
    self.assertIn(".choice-list{display:flex;flex-direction:column;gap:12px", compact)
    self.assertIn(".choice-card{width:100%;min-height:56px", compact)
    self.assertIn(".bottom-action{position:fixed", compact)
    self.assertIn("padding-bottom:calc(12px+env(safe-area-inset-bottom))", compact)

def test_quiz_layout_has_distinct_submission_and_answer_states(self):
    for selector in (
        ".choice-card.submitting",
        ".choice-card.correct",
        ".choice-card.wrong",
        ".answer-feedback",
        ".correct-label",
    ):
        self.assertIn(selector, self.quiz_wxss)
```

- [ ] **Step 2: Run the layout tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_miniprogram_ui.MiniProgramQuizUiContractTests.test_quiz_layout_uses_full_width_choices_and_fixed_action tests.test_miniprogram_ui.MiniProgramQuizUiContractTests.test_quiz_layout_has_distinct_submission_and_answer_states -v
```

Expected: FAIL because `quiz.wxss` contains only its placeholder comment.

- [ ] **Step 3: Give the page a quiz-specific root and safe scroll space**

Change the root WXML class to `screen quiz-screen`. In `miniprogram/pages/quiz/quiz.wxss`, start with:

```css
.quiz-screen {
  padding-left: 16px;
  padding-right: 16px;
  padding-bottom: calc(116px + env(safe-area-inset-bottom));
}

.choice-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
```

- [ ] **Step 4: Implement stable full-width option states**

Add page-local styles:

```css
.choice-card {
  width: 100%;
  min-height: 56px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin: 0;
  padding: 12px 14px;
  box-sizing: border-box;
  text-align: left;
  color: var(--ink);
  background: var(--card);
  border: 2px solid var(--line);
  border-radius: 14px;
}

.choice-card[disabled] { opacity: 1; }
.choice-card.submitting { border-color: var(--coral); background: var(--coral-soft); }
.choice-card.correct { border-color: #379482; background: var(--mint-soft); }
.choice-card.wrong { border-color: var(--danger); background: #fff1ef; }

.choice-key {
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f0ece3;
  font-weight: 800;
}

.choice-card.correct .choice-key { color: #fff; background: #379482; }
.choice-card.wrong .choice-key { color: #fff; background: var(--danger); }
.choice-copy { flex: 1; min-width: 0; padding-top: 2px; }
.correct-label { color: #28776c; font-size: 11px; font-weight: 800; padding-top: 5px; }
```

Add a reduced-motion-safe submission indicator:

```css
@keyframes choice-pulse {
  50% { opacity: 0.55; }
}

.choice-card.submitting .choice-key {
  animation: choice-pulse 700ms ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .choice-card.submitting .choice-key { animation: none; }
}
```

- [ ] **Step 5: Implement compact feedback, source, and safe-area action styles**

Add:

```css
.answer-feedback {
  margin-top: 16px;
  padding: 12px 14px;
  border-left: 4px solid var(--mint);
  border-radius: 12px;
  background: var(--card);
}

.feedback-title { font-size: 16px; font-weight: 800; }
.feedback-copy { margin-top: 4px; color: var(--muted); font-size: 14px; }
.source-toggle { margin-top: 8px; padding: 10px 0; color: var(--coral); background: transparent; font-weight: 700; }
.source-toggle::after { border: 0; }

.bottom-action {
  position: fixed;
  z-index: 20;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background: rgba(255, 254, 250, 0.98);
  border-top: 1px solid var(--line);
  box-shadow: 0 -8px 24px rgba(36, 41, 45, 0.08);
}

.bottom-hint { min-height: 48px; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 13px; }
```

Move the remaining quiz-only selectors from `app.wxss` into `quiz.wxss` with these values:

```css
.question-head { display: flex; align-items: center; justify-content: space-between; }
.status-pill { padding: 4px 8px; border-radius: 999px; background: var(--card); border: 1px solid var(--line); font-size: 11px; font-weight: 700; }
.question { margin: 24px 0 16px; font-size: 19px; line-height: 1.55; font-weight: 700; }
.source-drawer { margin: 8px 0 16px; padding: 12px; border: 1px dashed var(--line); border-radius: 14px; background: var(--card); font-size: 13px; }
```

Remove the old `.choice-card`, `.choice-key`, `.feedback`, `.source-drawer`, `.question`, `.question-head`, and `.status-pill` declarations from `app.wxss`. Do not leave duplicate selectors whose specificity can override the new state styles.

- [ ] **Step 6: Run the focused UI contracts and existing prototype tests**

Run:

```bash
python3 -m unittest tests.test_miniprogram_ui tests.test_prototypes -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit the quiz layout**

```bash
git add tests/test_miniprogram_ui.py miniprogram/pages/quiz/quiz.wxml miniprogram/pages/quiz/quiz.wxss miniprogram/app.wxss
git commit -m "style: expand quiz choices and pin next action"
```

---

### Task 5: Apply Balanced Button Spacing Across Existing Pages

**Files:**
- Modify: `tests/test_miniprogram_ui.py`
- Modify: `miniprogram/app.wxss`
- Modify: `miniprogram/pages/result/result.wxml`

**Interfaces:**
- Consumes: existing shared `.screen`, `.card`, `.input-card`, `.btn`, and `.btn-row` classes.
- Produces: reusable `16px` page margins, `12px` sibling-button gaps, and `20px` action-group separation for all current pages.

- [ ] **Step 1: Add failing global spacing and result-state tests**

Extend `setUp()`:

```python
self.app_wxss = (MINIPROGRAM / "app.wxss").read_text(encoding="utf-8")
self.result_wxml = (MINIPROGRAM / "pages/result/result.wxml").read_text(encoding="utf-8")
```

Add:

```python
def test_shared_spacing_uses_balanced_values(self):
    compact = "".join(self.app_wxss.split())
    self.assertIn(".screen{padding:18px16px96px", compact)
    self.assertIn(".card+.card{margin-top:16px", compact)
    self.assertIn("min-height:48px", compact)
    self.assertIn(".btn+.btn{margin-top:12px", compact)
    self.assertIn(".btn-row{display:flex;gap:12px;margin-top:20px", compact)
    self.assertIn(".btn-row.btn+.btn{margin-top:0", compact)
    self.assertIn(".input-card", self.app_wxss)
    self.assertIn("margin-bottom: 12px", self.app_wxss)

def test_no_wrong_result_does_not_repeat_again_action(self):
    self.assertIn('<block wx:if="{{result.wrong_question_ids.length}}">', self.result_wxml)
    self.assertIn("马上翻盘", self.result_wxml)
    self.assertIn('<block wx:else>', self.result_wxml)
    self.assertEqual(self.result_wxml.count("再考一篇"), 2)
```

The count is two in source because each mutually exclusive block owns one action; no rendered state contains two copies.

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_miniprogram_ui.MiniProgramQuizUiContractTests.test_shared_spacing_uses_balanced_values tests.test_miniprogram_ui.MiniProgramQuizUiContractTests.test_no_wrong_result_does_not_repeat_again_action -v
```

Expected: FAIL on the old 17px page margin, 9px row gap, missing sibling-button rule, and missing conditional result blocks.

- [ ] **Step 3: Apply shared balanced-spacing rules**

Update `app.wxss` to use:

```css
.screen { padding: 18px 16px 96px; box-sizing: border-box; }
.card + .card { margin-top: 16px; }
.btn { min-height: 48px; }
.btn + .btn { margin-top: 12px; }
.btn-row { display: flex; gap: 12px; margin-top: 20px; }
.btn-row .btn { flex: 1; margin-top: 0; }
.btn-row .btn + .btn { margin-top: 0; }
.input-card { margin-bottom: 12px; }
```

Keep the existing button colors, borders, and focus behavior. Replace the old `96rpx` minimum button height with `48px` so the touch target does not shrink on a 320px viewport. Do not add margins inside quiz choices because they are managed by `.choice-list`.

- [ ] **Step 4: Make result actions mutually exclusive**

Replace the current result actions with:

```xml
<block wx:if="{{result.wrong_question_ids.length}}">
  <button class="btn" bindtap="onRetest">马上翻盘</button>
  <view class="btn-row">
    <button class="btn ghost" bindtap="onAgain">再考一篇</button>
    <button class="btn ghost" bindtap="onShare">分享结果</button>
  </view>
</block>
<block wx:else>
  <button class="btn" bindtap="onAgain">再考一篇</button>
  <button class="btn ghost" bindtap="onShare">分享结果</button>
</block>
```

- [ ] **Step 5: Run all local UI tests**

Run:

```bash
cd miniprogram && npm test
cd .. && python3 -m unittest tests.test_miniprogram_ui tests.test_prototypes -v
```

Expected: all Node and Python tests PASS.

- [ ] **Step 6: Commit the shared spacing pass**

```bash
git add tests/test_miniprogram_ui.py miniprogram/app.wxss miniprogram/pages/result/result.wxml
git commit -m "style: standardize mini program action spacing"
```

---

### Task 6: Verify the Full Flow and Close the UI TODO

**Files:**
- Modify: `TODO.md`
- Verify only: all files changed in Tasks 1–5

**Interfaces:**
- Consumes: all implementation and tests from Tasks 1–5.
- Produces: verified branch state and a closed repository UI work item.

- [ ] **Step 1: Run automated verification**

Run:

```bash
cd miniprogram && npm test
cd ..
python3 -m unittest tests/test_miniprogram_ui.py tests/test_prototypes.py -v
cd backend && pytest tests/ -q
cd ..
git diff --check
```

Expected:

- Node answer-state tests: PASS.
- Mini-program and prototype Python contracts: PASS.
- Backend fixture-only suite: PASS without reading `backend/.env` or calling DeepSeek.
- `git diff --check`: no output and exit code 0.

- [ ] **Step 2: Verify in WeChat Developer Tools simulator**

Import `/Users/liuziying/Projects/dema-ai-learn/.worktrees/ui-spacing-redesign` as the mini-program project, keep legal-domain validation disabled, and use the simulator against `127.0.0.1:8000`.

Check all of the following at 320px, 375px, and 390px widths:

1. A normal 3-option question fits the safe width with exactly 16px side margins.
2. One tap submits; there is no confirmation button.
3. A correct answer shows green border, check, and “回答正确”.
4. A wrong answer shows a red crossed selected option and a green checked correct option with “正确答案”.
5. Rapid repeated taps create only one visible submission.
6. Disabling the backend or network returns the page to a retryable state without revealing the answer.
7. Long question, option, explanation, and source text remain scrollable and are not covered by the bottom action.
8. “下一题” and “查看结果” stay above the safe area.
9. Quiz report and source toggles remain reachable.
10. Result with wrong answers shows “马上翻盘”, “再考一篇”, and “分享结果” once each.
11. Result without wrong answers shows “再考一篇” once and “分享结果” once.
12. Preview, retest completion, quota, delete confirmation, and record-detail pages show visible 12px gaps between adjacent buttons.

- [ ] **Step 3: Record the implementation commit and close `TODO.md`**

Run `git log -1 --format=%h` and copy the returned short hash. Replace the unchecked UI optimization line in `TODO.md` with the same text marked `[x]`, followed by `（关联提交：实际返回的短哈希）`. Do not write a symbolic value such as `HEAD`.

- [ ] **Step 4: Commit verification documentation**

```bash
git add TODO.md
git commit -m "docs: close mini program UI spacing task"
```

- [ ] **Step 5: Confirm the final branch state**

Run:

```bash
git status -sb
git log --oneline --decorate -6
git diff main...HEAD --check
```

Expected: clean `codex/ui-spacing-redesign` worktree, the design and plan commits plus the implementation commits visible, and no whitespace errors.
