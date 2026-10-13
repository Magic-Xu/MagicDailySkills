const { chromium } = require("playwright");
const { default: AxeBuilder } = require("@axe-core/playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");
const { once } = require("node:events");
const { createServer } = require("./server.cjs");
const artifacts = path.join(__dirname, ".artifacts");
const output = (name) => path.join(artifacts, name);
let b;
let server;
(async () => {
  await fs.mkdir(artifacts, { recursive: true });
  server = createServer();
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const url = `http://127.0.0.1:${server.address().port}`;
  b = await chromium.launch({
    headless: true,
    ...(process.env.PLAYWRIGHT_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHANNEL } : {}),
  });
  const report = [];
  for (const [name, width, height] of [
    ["desktop", 1440, 1000],
    ["mobile", 390, 844],
    ["tablet", 768, 1024],
    ["narrow", 320, 740],
    ["middle", 1024, 900],
  ]) {
    const context = await b.newContext({
      viewport: { width, height },
      deviceScaleFactor: name === "mobile" ? 2 : 1,
      isMobile: name === "mobile",
      hasTouch: name === "mobile",
    });
    const p = await context.newPage();
    const errors = [];
    p.on("pageerror", (e) => errors.push(e.message));
    const network = [];
    p.on("requestfailed", (r) => network.push(r.url()));
    await p.goto(url);
    await p.waitForTimeout(1300);
    const checkWidth = async () => {
      const m = await p.evaluate(() => ({
        width: innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        height: document.documentElement.scrollHeight,
      }));
      assert(
        m.scrollWidth <= m.width,
        `${name} overflow: ${JSON.stringify(m)}`,
      );
      return m;
    };
    const metrics = await checkWidth();
    await p.screenshot({ path: output(`${name}.png`), fullPage: true });
    if (name === "desktop")
      await p.screenshot({ path: output("hero.png") });
    const violations = [];
    async function audit(state) {
      const r = await new AxeBuilder({ page: p })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze();
      violations.push(
        ...r.violations.map((v) => ({
          state,
          id: v.id,
          impact: v.impact,
          nodes: v.nodes.map((n) => ({
            target: n.target,
            summary: n.failureSummary,
          })),
        })),
      );
    }
    await audit("default");
    await p.locator("#overview-tab").focus();
    await p.keyboard.press("ArrowRight");
    assert.equal(
      await p.locator("#trend-tab").getAttribute("aria-selected"),
      "true",
    );
    assert.equal(await p.locator("#trend-panel").isVisible(), true);
    await checkWidth();
    await audit("trend");
    await p.keyboard.press("ArrowLeft");
    assert.equal(await p.locator("#overview-panel").isVisible(), true);
    await p.locator("#feature-quota").focus();
    await p.keyboard.press(width <= 800 ? "ArrowRight" : "ArrowDown");
    assert.equal(
      await p.locator("#feature-reset").getAttribute("aria-selected"),
      "true",
    );
    assert.match(await p.locator("#feature-panel").innerText(), /02:18/);
    await checkWidth();
    await audit("reset");
    await p.locator("#feature-subscriptions").click();
    assert.match(await p.locator("#feature-panel").innerText(), /10 月 20 日/);
    await checkWidth();
    await audit("subscriptions");
    await p.locator("#feature-quota").click();
    const opener = p.locator(".site-header [data-open-demo]");
    await opener.click();
    assert.equal(await p.locator("dialog").isVisible(), true);
    await p.locator('[data-pick="gemini"]').click();
    assert.equal(await p.locator("#demo-number").textContent(), "84");
    await p.locator("#usage-slider").focus();
    await p.keyboard.press("Home");
    assert.equal(await p.locator("#demo-number").textContent(), "0");
    assert.match(await p.locator("#demo-status").textContent(), /已用完/);
    await p.keyboard.press("End");
    assert.equal(await p.locator("#demo-number").textContent(), "100");
    await p.locator("#reset-demo").click();
    assert.equal(await p.locator("#demo-number").textContent(), "84");
    await p.locator('[data-pick="claude"]').click();
    assert.equal(await p.locator("#demo-number").textContent(), "42");
    await audit("dialog");
    await checkWidth();
    const dialogBox = await p.locator("dialog").boundingBox();
    assert(
      dialogBox.x >= 0 && dialogBox.x + dialogBox.width <= width + 0.5,
      "dialog clipped horizontally",
    );
    if (name === "desktop" || name === "mobile")
      await p.screenshot({ path: output(`dialog-${name}.png`) });
    await p.keyboard.press("Escape");
    assert.equal(await p.locator("dialog").isVisible(), false);
    assert.equal(
      await opener.evaluate((el) => el === document.activeElement),
      true,
    );
    await p.locator('[data-service="chatgpt"]').click();
    assert.equal(await p.locator("#demo-number").textContent(), "68");
    await p.locator("#usage-slider").fill("12");
    await p.locator(".close-button").click();
    assert.equal(
      (
        await p.locator('[data-service="chatgpt"] .usage-value').innerText()
      ).replace(/\s/g, ""),
      "12%",
    );
    assert.equal(
      (await p.locator(".gauge-number strong").innerText()).replace(/\s/g, ""),
      "12%",
    );
    await p.locator('[data-service="chatgpt"]').click();
    await p.locator("#reset-demo").click();
    await p.locator(".close-button").click();
    assert.equal(
      (
        await p.locator('[data-service="chatgpt"] .usage-value').innerText()
      ).replace(/\s/g, ""),
      "68%",
    );
    const faq = p.locator("summary").first();
    await faq.click();
    assert.equal(await p.locator("details").first().getAttribute("open"), "");
    await audit("faq");
    await faq.click();
    await p.emulateMedia({ reducedMotion: "reduce" });
    assert.equal(
      await p
        .locator(".app-window")
        .evaluate((e) => getComputedStyle(e).animationName),
      "none",
    );
    assert.equal(errors.length, 0);
    assert.equal(network.length, 0);
    report.push({
      name,
      width,
      height,
      metrics,
      interactions: "passed",
      reducedMotion: "passed",
      pageErrors: errors,
      failedRequests: network,
      violations,
    });
    await fs.writeFile(
      output("checks.json"),
      JSON.stringify(report, null, 2),
    );
    await context.close();
  }
  await fs.writeFile(
    output("checks.json"),
    JSON.stringify(report, null, 2),
  );
  console.log(
    JSON.stringify(
      report.map((r) => ({
        name: r.name,
        interactions: r.interactions,
        metrics: r.metrics,
        violations: r.violations.map((v) => ({
          state: v.state,
          id: v.id,
          nodes: v.nodes.length,
        })),
      })),
      null,
      2,
    ),
  );
  if (report.some((r) => r.violations.length)) process.exitCode = 1;
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
}).finally(async () => {
  await b?.close();
  if (server) await new Promise((resolve) => server.close(resolve));
});
