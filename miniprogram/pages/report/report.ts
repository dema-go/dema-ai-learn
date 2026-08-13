import { api, errorMessage } from "../../services/api";

Page({
  data: {
    questionId: "",
    stem: "",
    picked: "",
    types: [
      { id: "no_evidence", icon: "🔎", name: "无依据", desc: "原文不能支持答案" },
      { id: "wrong_answer", icon: "✕", name: "答案错", desc: "正确选项或解析不对" },
      { id: "ambiguous", icon: "↔", name: "有歧义", desc: "不止一个合理答案" },
      { id: "too_easy", icon: "🫧", name: "太简单", desc: "没有检验理解" },
    ],
  },

  onLoad(query: Record<string, string>) {
    this.setData({
      questionId: query.questionId || "",
      stem: decodeURIComponent(query.stem || "这道题"),
    });
  },

  onPick(event: WechatMiniprogram.TouchEvent) {
    this.setData({ picked: event.currentTarget.dataset.id as string });
    wx.showToast({ title: "已选择", icon: "none" });
  },

  async onSubmit() {
    if (!this.data.picked) {
      wx.showToast({ title: "请先选择问题类型", icon: "none" });
      return;
    }
    try {
      await api.feedback(this.data.questionId, this.data.picked);
      wx.showToast({ title: "反馈已收到，谢谢你替考考把关", icon: "none" });
      setTimeout(() => wx.navigateBack(), 500);
    } catch (err) {
      wx.showToast({ title: errorMessage(err, "提交失败"), icon: "none" });
    }
  },
});
