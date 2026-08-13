import { api, errorMessage } from "../../services/api";

Page({
  data: { url: "", error: "" },

  onInput(event: WechatMiniprogram.Input) {
    this.setData({ url: event.detail.value, error: "" });
  },

  async onSubmit() {
    const url = this.data.url.trim();
    if (!url) {
      this.setData({ error: "请粘贴公开网页链接。" });
      return;
    }
    wx.showLoading({ title: "提交中", mask: true });
    try {
      const res = await api.generate({ source_type: "url", url });
      wx.hideLoading();
      wx.redirectTo({ url: `/pages/generation/generation?taskId=${res.task_id}` });
    } catch (err) {
      wx.hideLoading();
      this.setData({ error: errorMessage(err, "这个网页没法读取，请改用粘贴文本。") });
    }
  },
});
