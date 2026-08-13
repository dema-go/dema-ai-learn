import { api, errorMessage } from "../../services/api";

Page({
  data: {
    text: "",
    count: 0,
    error: "",
  },

  onInput(event: WechatMiniprogram.Input) {
    const text = event.detail.value || "";
    this.setData({ text, count: text.length, error: text.length > 8000 ? "超过 8000 字，请截取重点段落后再试。" : "" });
  },

  async onSubmit() {
    const text = this.data.text.trim();
    if (!text) {
      this.setData({ error: "还没有内容。请粘贴一段完整的文字。" });
      return;
    }
    if (text.length > 8000) {
      this.setData({ error: "超过 8000 字，请截取重点段落后再试。" });
      return;
    }
    wx.showLoading({ title: "提交中", mask: true });
    try {
      const res = await api.generate({ source_type: "text", text });
      wx.hideLoading();
      wx.redirectTo({ url: `/pages/generation/generation?taskId=${res.task_id}` });
    } catch (err) {
      wx.hideLoading();
      const message = errorMessage(err, "提交失败");
      if ((err as { error?: { code: string } })?.error?.code === "QUOTA_EXCEEDED") {
        wx.redirectTo({ url: "/pages/quota/quota" });
        return;
      }
      this.setData({ error: message });
    }
  },
});
