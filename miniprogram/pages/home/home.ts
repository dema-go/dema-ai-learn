import { api, errorMessage, HomeResponse, RecentItem } from "../../services/api";

Page({
  data: {
    home: {
      quota: { used: 0, limit: 3, reset_at: "" },
      primary_task: { type: "create" },
      recent: [],
      me: { streak_days: 0, stars: 0, completed_count: 0 },
    } as HomeResponse,
    eyebrow: "第一次见",
    title: "你说看完了？\n那我可要出题了。",
    desc: "粘贴刚读的内容，3 分钟看看自己真懂了没。",
    speech: "",
    primaryText: "考我一下",
    kaokao: "/assets/kaokao-happy.svg",
  },

  onShow() {
    this.load();
  },

  async load() {
    try {
      const home = await api.home();
      const task = home.primary_task;
      let eyebrow = "第一次见";
      let title = "你说看完了？\n那我可要出题了。";
      let desc = "粘贴刚读的内容，3 分钟看看自己真懂了没。";
      let speech = "";
      let primaryText = "考我一下";
      let kaokao = "/assets/kaokao-happy.svg";
      if (task.type === "retest") {
        eyebrow = "今天的头号任务";
        title = `${task.wrong_count || 0} 道错题\n等你翻盘`;
        desc = `来自《${task.title || "上一篇材料"}》· 约 2 分钟`;
        speech = "考考：昨天那几题，我可都替你记着呢。";
        primaryText = "马上雪耻";
        kaokao = "/assets/kaokao-thinking.svg";
      } else if (task.type === "continue") {
        eyebrow = "还没答完";
        title = "接着闯关\n从上次停下的地方";
        desc = `《${task.title || "进行中的材料"}》· 第 ${task.current_ordinal || 1} 题`;
        speech = "考考：这关我帮你留着。";
        primaryText = "继续闯关";
        kaokao = "/assets/kaokao-thinking.svg";
      }
      this.setData({ home, eyebrow, title, desc, speech, primaryText, kaokao });
    } catch (err) {
      wx.showToast({ title: errorMessage(err, "首页加载失败"), icon: "none" });
    }
  },

  onPrimary() {
    const task = this.data.home.primary_task;
    if (task.type === "retest" && task.quiz_id) {
      api.retest(task.quiz_id).then((res) => {
        wx.navigateTo({ url: `/pages/quiz/quiz?quizId=${res.quiz_id}&retest=1` });
      }).catch((err) => {
        wx.showToast({ title: errorMessage(err, "无法开始复测"), icon: "none" });
      });
      return;
    }
    if (task.type === "continue" && task.quiz_id) {
      wx.navigateTo({ url: `/pages/quiz/quiz?quizId=${task.quiz_id}` });
      return;
    }
    this.onCreate();
  },

  onCreate() {
    if (this.data.home.quota.used >= this.data.home.quota.limit) {
      wx.navigateTo({ url: "/pages/quota/quota" });
      return;
    }
    wx.navigateTo({ url: "/pages/input-picker/input-picker" });
  },

  onRecent(event: WechatMiniprogram.TouchEvent) {
    const item = event.currentTarget.dataset.item as RecentItem;
    if (item.status === "active") {
      wx.navigateTo({ url: `/pages/quiz/quiz?quizId=${item.quiz_id}` });
      return;
    }
    wx.navigateTo({ url: `/pages/record-detail/record-detail?quizId=${item.quiz_id}&materialId=${item.material_id}` });
  },
});
