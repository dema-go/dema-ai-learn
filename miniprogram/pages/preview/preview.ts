import { api, errorMessage, QuizResponse } from "../../services/api";

Page({
  data: {
    quiz: { id: "", title: "", question_count: 0, ai_notice: "AI 依据你的材料生成，可能有误" } as QuizResponse,
  },

  async onLoad(query: Record<string, string>) {
    try {
      const quiz = await api.quiz(query.quizId || "");
      this.setData({ quiz });
    } catch (err) {
      wx.showToast({ title: errorMessage(err, "题目加载失败"), icon: "none" });
    }
  },

  onStart() {
    wx.redirectTo({ url: `/pages/quiz/quiz?quizId=${this.data.quiz.id}` });
  },

  onBack() {
    wx.navigateBack();
  },
});
