import { api, errorMessage } from "../../services/api";

Page({
  data: { materialId: "", title: "" },

  onLoad(query: Record<string, string>) {
    this.setData({
      materialId: query.materialId || "",
      title: decodeURIComponent(query.title || "这份材料"),
    });
  },

  async onConfirm() {
    try {
      await api.deleteMaterial(this.data.materialId);
      wx.showToast({ title: "已删除且无法恢复", icon: "none" });
      setTimeout(() => wx.switchTab({ url: "/pages/records/records" }), 400);
    } catch (err) {
      wx.showToast({ title: errorMessage(err, "删除失败"), icon: "none" });
    }
  },

  onCancel() {
    wx.navigateBack();
  },
});
