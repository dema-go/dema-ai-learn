Page({
  onText() {
    wx.navigateTo({ url: "/pages/text-input/text-input" });
  },
  onUrl() {
    wx.navigateTo({ url: "/pages/url-input/url-input" });
  },
  onSoon() {
    wx.showToast({ title: "敬请期待", icon: "none" });
  },
});
