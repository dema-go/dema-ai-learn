import { api, errorMessage } from "../../services/api";

Page({
  data: {
    quizId: "",
    result: { correct: 0, total: 0, duration_seconds: 0, wrong_question_ids: [] as string[] },
  },

  onLoad(query: Record<string, string>) {
    const stored = (wx.getStorageSync("last_result") || {}) as {
      quizId?: string;
      correct?: number;
      total?: number;
      duration_seconds?: number;
      wrong_question_ids?: string[];
    };
    this.setData({
      quizId: query.quizId || stored.quizId || "",
      result: {
        correct: stored.correct || 0,
        total: stored.total || 0,
        duration_seconds: stored.duration_seconds || 0,
        wrong_question_ids: stored.wrong_question_ids || [],
      },
    });
  },

  async onRetest() {
    try {
      const res = await api.retest(this.data.quizId);
      wx.redirectTo({ url: `/pages/quiz/quiz?quizId=${res.quiz_id}&retest=1` });
    } catch (err) {
      wx.showToast({ title: errorMessage(err, "无法开始复测"), icon: "none" });
    }
  },

  onAgain() {
    wx.navigateTo({ url: "/pages/input-picker/input-picker" });
  },

  onShare() {
    wx.showToast({ title: "分享稍后开放", icon: "none" });
  },
});
