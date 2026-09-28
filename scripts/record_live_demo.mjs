import { chromium } from "../frontend/node_modules/playwright/index.mjs";
import { execSync } from "child_process";
import fs from "fs";
import path from "path";

const VIDEO_DIR = path.resolve("./demo-video");
if (!fs.existsSync(VIDEO_DIR)) {
  fs.mkdirSync(VIDEO_DIR, { recursive: true });
}

async function run() {
  console.log("🎬 Starting FixFlow 1080p Live Walkthrough Video Recording...");

  const browser = await chromium.launch({
    headless: true,
  });

  const context = await browser.newContext({
    recordVideo: {
      dir: VIDEO_DIR,
      size: { width: 1920, height: 1080 },
    },
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
  });

  const page = await context.newPage();

  // Helper for human-like smooth typing
  async function typeSlowly(selector, text, delay = 25) {
    await page.click(selector);
    await page.fill(selector, "");
    for (const char of text) {
      await page.type(selector, char, { delay });
    }
  }

  // Helper to pause
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  console.log("📍 Step 1: Navigating to FixFlow platform...");
  await page.goto("http://127.0.0.1:8000/app/", { waitUntil: "networkidle" });
  await sleep(2500);

  console.log("📍 Step 2: Typing custom freeform complaint into textarea...");
  // Highlight the query area
  await page.evaluate(() => {
    const q = document.querySelector("#query");
    q.scrollIntoView({ behavior: "smooth", block: "center" });
    q.style.transition = "box-shadow 0.3s ease";
    q.style.boxShadow = "0 0 0 3px rgba(37, 99, 235, 0.4)";
  });
  await sleep(1000);

  const customQuery = "My camera flickers and shows horizontal black lines when shooting video indoors";
  await typeSlowly("#query", customQuery, 30);
  await sleep(1500);

  console.log("📍 Step 3: Triggering 'Build plan' (Knowledge Auto-Retrieval + Gemini cold-path)...");
  await page.click("#build");

  // Wait for the plan result to render
  await page.waitForSelector("#result:not([hidden])", { timeout: 20000 });
  await sleep(3500);

  console.log("📍 Step 4: Testing sub-10ms Cache Hit on repeat request...");
  await page.click("#build");
  await sleep(3000);

  console.log("📍 Step 5: Expanding Pipeline Execution Trace...");
  await page.evaluate(() => {
    const trace = document.querySelector("#trace");
    if (trace) {
      trace.open = true;
      trace.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });
  await sleep(4000);

  console.log("📍 Step 6: Viewing Semantic Query Variations...");
  await page.evaluate(() => {
    const vars = document.querySelector("#variations-box");
    if (vars) {
      vars.open = true;
      vars.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });
  await sleep(3500);

  console.log("📍 Step 7: Scrolling to interactive Galaxy S24 phone simulation...");
  await page.evaluate(() => {
    const dev = document.querySelector("#section-device");
    if (dev) dev.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  await sleep(2000);

  console.log("📍 Step 8: Executing plan on simulated Galaxy S24...");
  const runBtn = await page.$("#run:not([disabled])");
  if (runBtn) {
    await page.click("#run");
    // Wait for the simulation animation to step through
    await sleep(7000);
  } else {
    console.log("Run button not enabled, waiting...");
    await sleep(3000);
  }

  console.log("📍 Step 9: Final overview of resolved troubleshooting steps...");
  await page.evaluate(() => {
    const plan = document.querySelector("#section-plan");
    if (plan) plan.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  await sleep(3500);

  console.log("💾 Closing browser and saving video...");
  await context.close();
  await browser.close();

  // Find the generated webm file
  const files = fs.readdirSync(VIDEO_DIR).filter((f) => f.endsWith(".webm"));
  if (files.length === 0) {
    throw new Error("No webm video generated!");
  }

  // Sort by modification time to get the latest
  files.sort((a, b) => {
    return fs.statSync(path.join(VIDEO_DIR, b)).mtimeMs - fs.statSync(path.join(VIDEO_DIR, a)).mtimeMs;
  });

  const latestWebm = path.join(VIDEO_DIR, files[0]);
  const outputMp4 = path.join(VIDEO_DIR, "FixFlow_Live_Walkthrough_1080p.mp4");

  console.log(`🔄 Transcoding ${files[0]} to broadcast-ready 1080p MP4 via FFmpeg...`);
  const ffmpegCmd = `ffmpeg -y -i "${latestWebm}" -c:v libx264 -pix_fmt yuv420p -crf 18 -preset fast "${outputMp4}"`;
  execSync(ffmpegCmd, { stdio: "inherit" });

  const stats = fs.statSync(outputMp4);
  console.log(`✅ Success! Video ready at: ${outputMp4} (${(stats.size / 1024 / 1024).toFixed(2)} MB)`);
}

run().catch((err) => {
  console.error("❌ Recording failed:", err);
  process.exit(1);
});
