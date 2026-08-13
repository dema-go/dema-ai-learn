import { api, errorMessage, MeStats } from "../../services/api";

Page({
  data: {
    me: { streak_days: 0, stars: 0, completed_count: 0, retest_count: 0 } as MeStats,
  },

  onShow() {
    api.me()
      .then((me) => this.setData({ me }))
      .catch((err) => wx.showToast({ title: errorMessage(err, "统计加载失败"), icon: "none" }));
  },

  onPrivacy() {
    wx.navigateTo({ url: "/pages/privacy/privacy" });
  },

  onHelp() {
    wx.navigateTo({ url: "/pages/help/help" });
  },
});
