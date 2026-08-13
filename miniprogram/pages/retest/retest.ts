Page({
  onHome() {
    wx.switchTab({ url: "/pages/home/home" });
  },
  onAgain() {
    wx.navigateTo({ url: "/pages/input-picker/input-picker" });
  },
});
