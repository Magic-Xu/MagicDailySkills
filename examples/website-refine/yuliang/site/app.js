const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
$$(".segments").forEach((el) => {
  const value = Number(el.dataset.percent);
  el.innerHTML = Array.from(
    { length: 30 },
    (_, i) => `<i${i < Math.round(value * 0.3) ? ' class="filled"' : ""}></i>`,
  ).join("");
});
function bindTabs(list, onSelect) {
  const tabs = $$("[role=tab]", list);
  const select = (tab) => {
    tabs.forEach((t) => {
      const active = t === tab;
      t.setAttribute("aria-selected", String(active));
      t.tabIndex = active ? 0 : -1;
    });
    onSelect(tab);
  };
  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => select(tab));
    tab.addEventListener("keydown", (e) => {
      const isVertical = list.getAttribute("aria-orientation") === "vertical";
      const next = isVertical ? "ArrowDown" : "ArrowRight",
        prev = isVertical ? "ArrowUp" : "ArrowLeft";
      let idx;
      if (e.key === next) idx = (i + 1) % tabs.length;
      else if (e.key === prev) idx = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") idx = 0;
      else if (e.key === "End") idx = tabs.length - 1;
      else return;
      e.preventDefault();
      tabs[idx].focus();
      select(tabs[idx]);
    });
  });
}
bindTabs($(".app-tabs"), (tab) => {
  $$("#overview-panel, #trend-panel").forEach(
    (p) => (p.hidden = p.id !== tab.getAttribute("aria-controls")),
  );
});
const featureOrientation = matchMedia("(max-width: 800px)");
const setFeatureOrientation = () =>
  $(".focus-choices").setAttribute(
    "aria-orientation",
    featureOrientation.matches ? "horizontal" : "vertical",
  );
setFeatureOrientation();
featureOrientation.addEventListener("change", setFeatureOrientation);
const featurePanel = $("#feature-panel");
const quotaHTML = featurePanel.innerHTML;
const visuals = {
  quota: quotaHTML,
  reset: `<div class="visual-top"><span><i class="small-blue-dot"></i> 把下一步，安排好</span><span>示例数据</span></div><div class="reset-illustration"><p class="reset-caption">CLAUDE · 距离下次重置</p><div class="reset-clock">02<span style="opacity:.4">:</span>18</div><p class="reset-caption">有了时间，工作就有了节奏。</p><div class="reset-time-list"><span>ChatGPT<strong>04:05 后</strong></span><span>Gemini<strong>明天 00:00</strong></span></div></div><div class="visual-bottom"><span><i class="small-blue-dot"></i> 各服务按独立周期展示</span><span>静态时间示例</span></div>`,
  subscriptions: `<div class="visual-top"><span><i class="small-blue-dot"></i> 每份订阅，都清楚</span><span>示例记录</span></div><div class="subscription-list"><div class="subscription-item"><strong>✳ Claude</strong><span>个人订阅 · 10 月 20 日续订</span></div><div class="subscription-item"><strong>◎ ChatGPT</strong><span>个人订阅 · 10 月 25 日续订</span></div><div class="subscription-item"><strong>✦ Gemini</strong><span>个人订阅 · 11 月 02 日续订</span></div></div><div class="visual-bottom"><span><i class="small-blue-dot"></i> 订阅和使用，放在一起看</span><span>无真实账单</span></div>`,
};
bindTabs($(".focus-choices"), (tab) => {
  featurePanel.setAttribute("aria-labelledby", tab.id);
  featurePanel.innerHTML = visuals[tab.dataset.feature];
  syncOverview();
});
const dialog = $("#demo-dialog");
const defaults = { claude: 42, chatgpt: 68, gemini: 84 };
let values = { ...defaults },
  selected = "claude",
  opener;
const names = {
  claude: "Claude · 当前会话",
  chatgpt: "ChatGPT · 当前周期",
  gemini: "Gemini · 今日额度",
};
function syncOverview() {
  const resetLabels = {
    claude: "2 小时 18 分后重置",
    chatgpt: "4 小时 05 分后重置",
    gemini: "明天零点重置",
  };
  $$(".usage-row").forEach((row) => {
    const key = row.dataset.service,
      value = values[key];
    $(".usage-value", row).innerHTML = `${value}<span>%</span>`;
    $(".usage-meta", row).firstChild.textContent = `剩余 ${value}%`;
    row.setAttribute(
      "aria-label",
      `${names[key]}，剩余 ${value}%，${resetLabels[key]}，查看详情`,
    );
    $$(".segments i", row).forEach((bar, i) =>
      bar.classList.toggle("filled", i < Math.round(value * 0.3)),
    );
  });
  const gauge = $(".gauge-number strong");
  if (gauge) {
    gauge.innerHTML = `${values.chatgpt}<span>%</span>`;
    $(".gauge-fill").style.strokeDasharray = `${values.chatgpt} 100`;
  }
}
function renderDemo() {
  syncOverview();
  const value = values[selected];
  $("#demo-service").textContent = names[selected];
  $("#demo-number").textContent = value;
  $("#usage-slider").value = value;
  $("#slider-output").textContent = `${value}%`;
  $("#demo-track-fill").style.width = `${value}%`;
  $("#demo-status").textContent =
    value === 0
      ? "当前示例额度已用完，可以查看其他服务。"
      : value <= 20
        ? `还剩 ${value}%，可以为下一项任务预留空间。`
        : `还剩 ${value}%，可以继续安排任务。`;
  $$("[data-pick]").forEach((b) =>
    b.setAttribute("aria-pressed", String(b.dataset.pick === selected)),
  );
}
function openDemo(service, button) {
  selected = service || "claude";
  opener = button;
  renderDemo();
  dialog.showModal();
}
$$("[data-open-demo]").forEach((b) =>
  b.addEventListener("click", () => openDemo("claude", b)),
);
$$("[data-service]").forEach((b) =>
  b.addEventListener("click", () => openDemo(b.dataset.service, b)),
);
$(".close-button").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (e) => {
  if (e.target === dialog) {
    const r = dialog.getBoundingClientRect();
    if (
      e.clientX < r.left ||
      e.clientX > r.right ||
      e.clientY < r.top ||
      e.clientY > r.bottom
    )
      dialog.close();
  }
});
dialog.addEventListener("close", () => opener?.focus());
$$("[data-pick]").forEach((b) =>
  b.addEventListener("click", () => {
    selected = b.dataset.pick;
    renderDemo();
  }),
);
$("#usage-slider").addEventListener("input", (e) => {
  values[selected] = Number(e.target.value);
  renderDemo();
});
$("#reset-demo").addEventListener("click", () => {
  values = { ...defaults };
  renderDemo();
});
