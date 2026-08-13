import { api, errorMessage, RecentItem } from "../../services/api";

Page({
  data: { items: [] as RecentItem[] },

  onShow() {
    api.recent("retest")
      .then((res) => this.setData({ items: res.items }))
      .catch((err) => wx.showToast({ title: errorMessage(err, "错题加载失败"), icon: "none" }));
  },

  async onRetest(event: WechatMiniprogram.TouchEvent) {
    try {
      const res = await api.retest(event.currentTarget.dataset.id as string);
      wx.navigateTo({ url: `/pages/quiz/quiz?quizId=${res.quiz_id}&retest=1` });
    } catch (err) {
      wx.showToast({ title: errorMessage(err, "无法开始复测"), icon: "none" });
    }
  },

  onCreate() {
    wx.navigateTo({ url: "/pages/input-picker/input-picker" });
  },
});
