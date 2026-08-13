Page({
  onRetest() {
    wx.navigateTo({ url: "/pages/wrong-book/wrong-book" });
  },
  onRecords() {
    wx.switchTab({ url: "/pages/records/records" });
  },
});
