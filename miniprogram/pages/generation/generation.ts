import { api, errorMessage, TaskResponse } from "../../services/api";

Page({
  data: {
    taskId: "",
    percent: 20,
    stages: [
      { label: "正在理解原文", cls: "" },
      { label: "正在抓住重点", cls: "" },
      { label: "正在生成题目", cls: "" },
      { label: "正在检查答案", cls: "" },
    ],
  },
  timer: 0 as number,

  onLoad(query: Record<string, string>) {
    this.setData({ taskId: query.taskId || "" });
    this.poll();
    this.timer = setInterval(() => this.poll(), 1500) as unknown as number;
  },

  onUnload() {
    if (this.timer) clearInterval(this.timer);
  },

  async poll() {
    if (!this.data.taskId) return;
    try {
      const task = await api.task(this.data.taskId);
      this.render(task);
      if (task.status === "succeeded" || task.status === "degraded") {
        if (this.timer) clearInterval(this.timer);
        wx.redirectTo({ url: `/pages/preview/preview?quizId=${task.quiz_id}` });
      } else if (task.status === "failed") {
        if (this.timer) clearInterval(this.timer);
        wx.showModal({
          title: "这篇材料没法出题",
          content: task.error || "请换一段观点更完整的文字。",
          confirmText: "返回修改",
          success: () => wx.navigateBack(),
        });
      }
    } catch (err) {
      wx.showToast({ title: errorMessage(err, "生成状态读取失败"), icon: "none" });
    }
  },

  render(task: TaskResponse) {
    const map: Record<string, number> = {
      extracting: 0,
      pending: 0,
      planning: 1,
      generating: 2,
      validating: 3,
    };
    const idx = map[task.stage] ?? 0;
    const stages = [
      { label: "正在理解原文", cls: idx > 0 ? "done" : idx === 0 ? "active" : "" },
      { label: "正在抓住重点", cls: idx > 1 ? "done" : idx === 1 ? "active" : "" },
      { label: task.progress.includes("第") ? task.progress : "正在生成题目", cls: idx > 2 ? "done" : idx === 2 ? "active" : "" },
      { label: "正在检查答案", cls: idx >= 3 ? "active" : "" },
    ];
    this.setData({ stages, percent: Math.min(90, 20 + idx * 22) });
  },

  onHome() {
    wx.switchTab({ url: "/pages/home/home" });
  },
});
