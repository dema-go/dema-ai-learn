Page({
  onItem(event: WechatMiniprogram.TouchEvent) {
    wx.showToast({ title: event.currentTarget.dataset.msg as string, icon: "none" });
  },
  onPrivacy() {
    wx.navigateTo({ url: "/pages/privacy/privacy" });
  },
});
