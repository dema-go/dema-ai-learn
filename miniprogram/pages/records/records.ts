import { api, errorMessage, RecentItem } from "../../services/api";

Page({
  data: { items: [] as RecentItem[] },

  onShow() {
    api.recent()
      .then((res) => this.setData({ items: res.items }))
      .catch((err) => wx.showToast({ title: errorMessage(err, "记录加载失败"), icon: "none" }));
  },

  onOpen(event: WechatMiniprogram.TouchEvent) {
    const item = event.currentTarget.dataset.item as RecentItem;
    if (item.status === "active") {
      wx.navigateTo({ url: `/pages/quiz/quiz?quizId=${item.quiz_id}` });
      return;
    }
    wx.navigateTo({ url: `/pages/record-detail/record-detail?quizId=${item.quiz_id}&materialId=${item.material_id}` });
  },

  onCreate() {
    wx.navigateTo({ url: "/pages/input-picker/input-picker" });
  },
});
