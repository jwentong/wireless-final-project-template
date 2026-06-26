from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from src.pipeline import run_pipeline


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>无线通信基带仿真系统</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #081116;
      --panel: #0f1b22;
      --panel-strong: #13252e;
      --panel-soft: #17262f;
      --ink: #edf8f7;
      --muted: #8da5ad;
      --line: #28414b;
      --line-hot: rgba(57, 215, 200, .42);
      --accent: #39d7c8;
      --accent-strong: #8ff7ec;
      --accent-soft: rgba(57, 215, 200, .14);
      --amber: #f7b955;
      --warn: #f7b955;
      --ok: #74e083;
      --danger: #ff7777;
      --shadow: 0 22px 60px rgba(0, 0, 0, .42);
      --mono: "Cascadia Mono", "Consolas", "SFMono-Regular", monospace;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", Arial, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 18% 8%, rgba(57, 215, 200, .16), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(247, 185, 85, .10), transparent 26%),
        var(--bg);
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(57, 215, 200, .055) 1px, transparent 1px),
        linear-gradient(90deg, rgba(57, 215, 200, .045) 1px, transparent 1px);
      background-size: 48px 48px;
      mask-image: linear-gradient(to bottom, black, transparent 78%);
    }
    .scope-grid {
      position: relative;
      overflow: hidden;
      background:
        linear-gradient(90deg, rgba(57, 215, 200, .07) 1px, transparent 1px),
        linear-gradient(rgba(57, 215, 200, .07) 1px, transparent 1px),
        linear-gradient(135deg, rgba(15, 27, 34, .96), rgba(19, 37, 46, .96));
      background-size: 28px 28px, 28px 28px, auto;
    }
    .scope-grid::after {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(90deg, transparent, rgba(57, 215, 200, .16), transparent);
      transform: translateX(-100%);
      animation: sweep 5.6s ease-in-out infinite;
      pointer-events: none;
    }
    @keyframes sweep { 45%, 100% { transform: translateX(120%); } }
    header { padding: 18px 20px 0; }
    .header-inner {
      max-width: 1500px;
      margin: 0 auto;
      border: 1px solid var(--line-hot);
      border-radius: 8px;
      padding: 16px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 18px;
      box-shadow: var(--shadow);
    }
    .eyebrow { margin: 0 0 5px; color: var(--accent); font-family: var(--mono); font-size: 12px; }
    h1 { margin: 0; font-size: clamp(23px, 3vw, 36px); font-weight: 800; letter-spacing: 0; }
    header p { margin: 8px 0 0; color: #b8ccd1; line-height: 1.6; max-width: 980px; }
    .mode-badge {
      min-width: 176px;
      border: 1px solid var(--line-hot);
      border-radius: 8px;
      padding: 12px 14px;
      background: rgba(8, 17, 22, .78);
      text-align: center;
      font-family: var(--mono);
      font-weight: 800;
      color: var(--accent-strong);
      box-shadow: inset 0 0 18px rgba(57, 215, 200, .12);
    }
    main { max-width: 1500px; margin: 0 auto; padding: 16px 20px 22px; display: grid; grid-template-columns: 390px minmax(0, 1fr); gap: 16px; }
    section, .panel {
      background: rgba(15, 27, 34, .94);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-width: 0;
      box-shadow: 0 14px 36px rgba(0, 0, 0, .28);
    }
    .console-panel { border-color: rgba(57, 215, 200, .28); }
    h2 { margin: 0 0 12px; font-size: 17px; letter-spacing: 0; }
    h3 { margin: 0 0 8px; font-size: 15px; letter-spacing: 0; }
    .section-kicker { color: var(--accent); font-family: var(--mono); font-size: 12px; margin: 0 0 5px; }
    label { display: block; margin: 10px 0 5px; color: var(--muted); font-size: 13px; }
    textarea, input, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 11px;
      font: inherit;
      background: #0b171d;
      color: var(--ink);
      outline: none;
    }
    textarea:focus, input:focus, select:focus, button:focus-visible {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(57, 215, 200, .18);
    }
    textarea { min-height: 164px; resize: vertical; line-height: 1.6; }
    select { cursor: pointer; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }
    .quick-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px; }
    .demo-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 10px 0 4px; }
    .demo-button { min-height: 46px; padding: 9px 10px; text-align: left; color: var(--ink); background: #0b171d; border: 1px solid var(--line); }
    .demo-button:hover { border-color: var(--amber); background: rgba(247, 185, 85, .10); }
    .range-row { display: grid; grid-template-columns: minmax(0, 1fr) 82px; gap: 9px; align-items: end; }
    input[type="range"] { accent-color: var(--accent); padding: 0; height: 36px; }
    button {
      border: 1px solid rgba(57, 215, 200, .34);
      border-radius: 6px;
      padding: 11px 12px;
      font: inherit;
      font-weight: 800;
      cursor: pointer;
      color: #041113;
      background: linear-gradient(180deg, var(--accent-strong), var(--accent));
    }
    button:hover { filter: brightness(1.08); }
    button:disabled { opacity: .65; cursor: wait; }
    .secondary { color: #1b1200; border-color: rgba(247, 185, 85, .5); background: linear-gradient(180deg, #ffd98b, var(--amber)); }
    .ghost { color: var(--ink); background: rgba(23, 38, 47, .92); border: 1px solid var(--line); }
    .ghost:hover { border-color: var(--accent); background: rgba(57, 215, 200, .10); }
    .run-button { width: 100%; margin-top: 12px; font-size: 16px; min-height: 48px; }
    .status {
      min-height: 26px;
      margin-top: 10px;
      color: var(--accent-strong);
      font-family: var(--mono);
      font-size: 13px;
      overflow-wrap: anywhere;
    }
    .log-panel { border: 1px solid var(--line); border-radius: 8px; background: #071015; padding: 10px; margin-top: 10px; }
    .log-panel h3 { color: var(--accent); font-family: var(--mono); font-size: 12px; text-transform: uppercase; }
    .log-list { margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; max-height: 142px; overflow: auto; }
    .log-list li { color: #d9e8ea; font-family: var(--mono); font-size: 12px; line-height: 1.45; }
    .stage-control { border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: #0b171d; margin-top: 8px; }
    .stage-control strong { display: block; font-size: 13px; margin-bottom: 4px; color: var(--amber); }
    .stage-control p { margin: 0; color: var(--muted); font-size: 12px; line-height: 1.5; }
    .right-stack { display: grid; gap: 14px; }
    .dashboard { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 10px; }
    .metric-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: linear-gradient(180deg, #10202a, #0b171d);
      min-height: 96px;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, .04);
    }
    .metric-card span { display: block; color: var(--muted); font-size: 12px; margin-bottom: 9px; }
    .metric-card strong { display: block; font-family: var(--mono); font-size: 26px; line-height: 1.1; word-break: break-word; color: var(--amber); }
    .metric-card.good { border-color: rgba(116, 224, 131, .35); }
    .metric-card.good strong { color: var(--ok); }
    .metric-card.warn { border-color: rgba(247, 185, 85, .38); }
    .metric-card.warn strong { color: var(--warn); }
    .comparison { margin-top: 12px; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; background: #0b171d; }
    .comparison h3 { padding: 10px 12px; margin: 0; border-bottom: 1px solid var(--line); color: var(--accent-strong); }
    .comparison table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .comparison th, .comparison td { padding: 9px 10px; border-bottom: 1px solid rgba(40, 65, 75, .76); text-align: left; }
    .comparison th { color: var(--muted); font-family: var(--mono); font-size: 12px; font-weight: 700; }
    .comparison td:last-child { color: var(--ok); font-family: var(--mono); }
    .evidence-board { margin-top: 12px; display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 10px; }
    .evidence-card { border: 1px solid var(--line); border-radius: 8px; background: #0b171d; padding: 10px; min-height: 152px; }
    .evidence-card h3 { color: var(--accent-strong); margin-bottom: 6px; }
    .evidence-card p { color: var(--muted); margin: 8px 0 0; font-size: 12px; line-height: 1.45; }
    .mini-visual { height: 76px; border: 1px solid rgba(57, 215, 200, .18); border-radius: 6px; background: #071015; position: relative; overflow: hidden; }
    .constellation-mini::before, .constellation-mini::after { content: ""; position: absolute; width: 9px; height: 9px; border-radius: 50%; background: var(--accent); box-shadow: 38px 0 0 var(--accent), 0 38px 0 var(--accent), 38px 38px 0 var(--accent); left: calc(50% - 24px); top: calc(50% - 24px); }
    .ber-mini::before { content: ""; position: absolute; left: 12px; right: 12px; top: 16px; height: 42px; border-left: 3px solid var(--amber); border-bottom: 3px solid var(--accent); transform: skewY(-18deg); transform-origin: left bottom; }
    .sync-mini::before { content: ""; position: absolute; left: 16px; bottom: 12px; width: 10px; height: 42px; background: var(--amber); box-shadow: 20px 24px 0 rgba(57,215,200,.45), 40px 8px 0 var(--accent), 60px 28px 0 rgba(57,215,200,.35), 80px 22px 0 rgba(57,215,200,.35); }
    .text-mini::before { content: "Test.txt = received.txt"; position: absolute; inset: 0; display: grid; place-items: center; color: var(--ok); font-family: var(--mono); font-size: 12px; }
    .result-hero { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(300px, .9fr); gap: 12px; align-items: stretch; }
    .plot-main, .plot-side figure, .text-card, .json-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #0b171d;
      padding: 10px;
      margin: 0;
    }
    .plot-main { border-color: rgba(57, 215, 200, .35); }
    .plot-main img {
      width: 100%;
      display: block;
      min-height: 430px;
      max-height: 520px;
      object-fit: contain;
      background: #071015;
      border: 1px solid rgba(57, 215, 200, .16);
      border-radius: 6px;
    }
    .plot-caption, figcaption { margin-top: 8px; color: var(--muted); font-size: 13px; line-height: 1.45; }
    .plot-side { display: grid; gap: 12px; }
    .plot-side img {
      width: 100%;
      display: block;
      min-height: 190px;
      object-fit: contain;
      background: #071015;
      border: 1px solid rgba(57, 215, 200, .12);
      border-radius: 6px;
    }
    .tabs { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; border-bottom: 1px solid var(--line); padding-bottom: 10px; }
    .tab-button { width: auto; margin: 0; padding: 8px 12px; background: #0b171d; color: var(--ink); border: 1px solid var(--line); }
    .tab-button.active { background: var(--accent-soft); color: var(--accent-strong); border-color: var(--accent); box-shadow: inset 0 0 18px rgba(57, 215, 200, .10); }
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }
    .chain-layout { display: grid; grid-template-columns: minmax(240px, 340px) minmax(0, 1fr); gap: 12px; }
    .flow-steps { display: grid; gap: 7px; align-content: start; border-left: 2px solid rgba(57, 215, 200, .18); padding-left: 10px; }
    .flow-step { width: 100%; margin: 0; padding: 9px 10px; text-align: left; background: #0b171d; color: var(--ink); border: 1px solid var(--line); border-radius: 7px; font-family: var(--mono); font-size: 12px; }
    .flow-step.active { background: var(--accent-soft); border-color: var(--accent); color: var(--accent-strong); }
    .stage-detail { border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #0b171d; min-height: 290px; }
    .diagram-box { border: 1px solid var(--line); border-radius: 8px; background: #071015; min-height: 190px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
    .diagram-box svg { width: 100%; max-height: 190px; }
    .stage-detail p { color: var(--muted); line-height: 1.55; }
    code { background: #071015; border: 1px solid var(--line); border-radius: 5px; padding: 2px 6px; color: var(--accent-strong); font-family: var(--mono); }
    .chips, .kv { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 9px; }
    .chips span, .kv span { border: 1px solid var(--line); border-radius: 999px; background: var(--panel-soft); padding: 4px 8px; font-size: 12px; overflow-wrap: anywhere; color: #d8e7ea; }
    .trace { display: grid; gap: 9px; }
    .trace-card { border-left: 4px solid var(--accent); border-radius: 8px; border-top: 1px solid var(--line); border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); background: #0b171d; padding: 10px 12px; }
    .trace-card p { margin: 0 0 7px; color: var(--muted); font-size: 12px; }
    .text-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .diff-card { grid-column: 1 / -1; }
    .diff-output mark { background: rgba(247, 185, 85, .24); color: #ffe3a5; border-radius: 3px; padding: 0 2px; }
    pre { margin: 0; white-space: pre-wrap; word-break: break-word; background: #071015; color: #e5f5f3; border: 1px solid var(--line); border-radius: 8px; padding: 12px; min-height: 180px; max-height: 360px; overflow: auto; line-height: 1.5; font-family: var(--mono); }
    @media (max-width: 1100px) {
      .header-inner, main, .result-hero, .chain-layout, .text-grid { grid-template-columns: 1fr; }
      .dashboard { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      .evidence-board { grid-template-columns: repeat(2, minmax(140px, 1fr)); }
      .plot-main img { min-height: 300px; }
      .mode-badge { width: 100%; }
    }
    @media (max-width: 640px) {
      header { padding: 10px 10px 0; }
      main { padding: 10px; }
      .grid, .quick-actions, .dashboard { grid-template-columns: 1fr; }
      .evidence-board { grid-template-columns: 1fr; }
      section, .panel { padding: 12px; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; }
    }
  </style>
</head>
<body>
  <header><div class="header-inner scope-grid"><div><p class="eyebrow">LAB LINK / BASEBAND CONSOLE</p><h1>无线通信基带仿真系统</h1><p>实验室链路：文本载荷经过源编码、扰码、信道编码、组帧、调制、信道、同步、解调、译码和恢复，并实时观测恢复结果与关键图表。</p></div><div class="mode-badge" id="modeBadge">等待运行</div></div></header>
  <main>
    <section class="console-panel">
      <p class="section-kicker">TX CONTROL</p>
      <h2>发射机控制台</h2>
      <div class="quick-actions"><button type="button" class="ghost" id="presetBase">一键基础验收</button><button type="button" class="secondary" id="presetAdvanced">一键高级模块</button></div>
      <div class="demo-grid" aria-label="一键Demo按钮">
        <button type="button" class="demo-button" data-demo="stable">12dB稳定通信演示</button>
        <button type="button" class="demo-button" data-demo="low">低SNR失败演示</button>
        <button type="button" class="demo-button" data-demo="rayleigh">Rayleigh衰落演示</button>
        <button type="button" class="demo-button" data-demo="advanced">高级模式全开</button>
      </div>
      <label for="text">发送文本</label><textarea id="text">无线通信技术课程要求学生理解调制、编码、信道和接收机处理。本界面用于演示 QPSK、AWGN/Rayleigh 信道、OFDM、分集、Viterbi、自适应调制、同步和端到端恢复。</textarea>
      <label for="snrRange">SNR滑块 / dB</label><div class="range-row"><input id="snrRange" type="range" min="0" max="24" value="12" step="1"><input id="snr" type="number" value="12" step="1" min="0" max="24" aria-label="SNR 数值"></div>
      <div class="grid"><div><label for="seed">随机种子</label><input id="seed" type="number" value="2026" step="1"></div><div><label for="sourceCodec">源编码</label><select id="sourceCodec"><option value="utf8">UTF-8 文本转比特</option></select></div></div>
      <div class="grid"><div><label for="scramble">扰码 / 加密</label><select id="scramble"><option value="pn-xor">PN XOR 扰码</option><option value="none">关闭，仅演示</option></select></div><div><label for="channel">无线信道</label><select id="channel"><option value="awgn">AWGN</option><option value="rayleigh">Rayleigh + 均衡</option></select></div></div>
      <div class="grid"><div><label for="coding">信道编码</label><select id="coding"><option value="repetition3">重复 3 次编码</option><option value="conv">卷积码 + Viterbi</option><option value="none">关闭，仅演示</option></select></div><div><label for="mod">调制方式</label><select id="mod"><option value="qpsk">Gray QPSK</option><option value="adaptive">自适应调制</option><option value="bpsk">BPSK</option><option value="16qam">16-QAM</option></select></div></div>
      <div class="grid"><div><label for="diversity">接收分集</label><select id="diversity"><option value="none">关闭</option><option value="mrc2">2 分支 MRC</option></select></div><div><label for="ofdm">OFDM</label><select id="ofdm"><option value="false">关闭</option><option value="true">开启，FFT 64 / CP 16</option></select></div></div>
      <button id="run" class="run-button">运行仿真并刷新结果</button><div class="status" id="status"></div>
      <div class="log-panel"><h3>实时日志</h3><ul class="log-list" id="demoLog"><li>[READY] 等待运行仿真链路</li></ul></div>
      <div class="stage-control"><strong>答辩提示</strong><p>基础验收使用 QPSK + AWGN；高级模块使用 adaptive + Rayleigh + conv + MRC2 + OFDM。</p></div>
    </section>
    <div class="right-stack">
      <section><p class="section-kicker">RX READOUT</p><h2>链路读数</h2><div class="dashboard" id="dashboard"></div></section>
      <section>
        <p class="section-kicker">RX OBSERVATION</p><h2>接收机观测窗</h2>
        <div class="tabs"><button type="button" class="tab-button active" data-tab="resultTab">突出结果图</button><button type="button" class="tab-button" data-tab="chainTab">实验室链路</button><button type="button" class="tab-button" data-tab="dataTab">恢复文本与 JSON</button></div>
        <div class="tab-panel active" id="resultTab"><div class="result-hero"><div class="plot-main"><h3>主图：接收星座图</h3><img id="constellation" alt="接收星座图"><div class="plot-caption">星座点越集中，说明调制符号受噪声和衰落影响越小；高级模式下也可观察 16-QAM/OFDM 后的恢复效果。</div></div><div class="plot-side"><figure><h3>信号诊断：BER-SNR 曲线</h3><img id="ber" alt="BER-SNR 曲线"><figcaption>展示 SNR 升高时误比特率下降趋势。</figcaption></figure><figure><h3>信号诊断：同步相关峰值</h3><img id="sync" alt="同步相关峰值"><figcaption>峰值位置对应接收端检测到的帧起点。</figcaption></figure></div></div><div class="evidence-board" aria-label="信号证据板"><div class="evidence-card"><h3>信号证据板</h3><div class="mini-visual constellation-mini"></div><p>星座聚类：四个点云对应 QPSK 判决区域，点云越紧说明噪声越小。</p></div><div class="evidence-card"><h3>误码率下降</h3><div class="mini-visual ber-mini"></div><p>BER-SNR 曲线证明信噪比升高后误码率下降，是调制可靠性的量化证据。</p></div><div class="evidence-card"><h3>同步峰值锁定</h3><div class="mini-visual sync-mini"></div><p>同步相关峰值对应帧起点，证明接收端没有假设天然同步。</p></div><div class="evidence-card"><h3>文本恢复证明</h3><div class="mini-visual text-mini"></div><p>received.txt 与输入文本一致时，整条链路从编码到译码全部闭环。</p></div></div><div class="comparison"><h3>方案对比</h3><table><thead><tr><th>方案</th><th>核心设计</th><th>答辩证据</th><th>恢复结果</th></tr></thead><tbody><tr><td>AWGN + QPSK</td><td>基础统一验收</td><td>12 dB / BER 0 / CRC pass</td><td>通过</td></tr><tr><td>Rayleigh</td><td>衰落 + 均衡</td><td>展示信道扩展能力</td><td>通过</td></tr><tr><td>Conv + Viterbi</td><td>提高纠错能力</td><td>coding_gain.png</td><td>通过</td></tr><tr><td>OFDM + MRC2</td><td>高级模块全开</td><td>advanced-all 实验</td><td>通过</td></tr></tbody></table></div></div>
        <div class="tab-panel" id="chainTab"><div class="chain-layout"><div class="flow-steps" id="flowSteps"></div><div class="stage-detail"><div class="diagram-box" id="stageDiagram"></div><h3 id="stageTitle">链路阶段</h3><p id="stageText">点击左侧阶段查看说明。</p><p><code id="stageFormula">等待运行</code></p><div class="chips" id="stageLive"></div></div></div><h3 style="margin-top:14px">完整链路追踪</h3><div class="trace" id="trace"></div></div>
        <div class="tab-panel" id="dataTab"><div class="text-grid"><div class="text-card"><h3>输入文本 Test.txt</h3><pre id="sourcePreview">等待运行。</pre></div><div class="text-card"><h3>恢复文本 received.txt</h3><pre id="received">等待运行。</pre></div><div class="diff-card text-card"><h3>文本对比</h3><pre class="diff-output" id="diffOutput">运行后显示输入与恢复文本差异。</pre></div><div class="json-card"><h3>metrics.json</h3><pre id="json">等待运行。</pre></div></div></div>
      </section>
    </div>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    const traceIgnore = new Set(["name", "detail"]);
    let latestStages = [];
    let activeLesson = 0;
    const source_stage_name = "源码阶段名称映射";
    const stageNameMap = {"Source Encode":"源编码","Scramble / Encrypt":"扰码 / 加密","Channel Encode":"信道编码","Frame Build":"组帧","QPSK Modulate":"QPSK 调制","Modulate":"调制","OFDM Modulate":"OFDM 调制","Wireless Channel":"无线信道","Synchronization":"同步捕获","OFDM Demodulate":"OFDM 解调","QPSK Demodulate":"QPSK 解调","Demodulate":"解调","Channel Decode":"信道译码","Descramble / Decrypt":"解扰 / 解密","Source Decode":"源解码","Metrics / Plots":"指标与图表"};
    const stageDetailMap = {"Source Encode":"将 UTF-8 文本转换为大端比特流。","Scramble / Encrypt":"用 PN 序列异或扰码，接收端可逆恢复。","Channel Encode":"按所选纠错码加入冗余，提高抗噪能力。","Frame Build":"加入前导、长度、载荷和 CRC，形成可同步的数据帧。","QPSK Modulate":"把比特映射为归一化星座符号。","Modulate":"把比特映射为所选调制方式的星座符号。","OFDM Modulate":"把星座符号装入子载波并添加循环前缀。","Wireless Channel":"加入随机前置偏移，并通过 AWGN 或 Rayleigh 信道。","Synchronization":"用前导相关峰值估计帧起点。","OFDM Demodulate":"移除循环前缀并通过 FFT 恢复子载波符号。","QPSK Demodulate":"根据星座判决把接收符号还原为比特。","Demodulate":"根据所选调制方式进行硬判决解调。","Channel Decode":"用译码器纠错并恢复原始载荷比特。","Descramble / Decrypt":"再次异或同一 PN 序列，恢复源比特。","Source Decode":"按 UTF-8 将比特流恢复为文本。","Metrics / Plots":"写出 BER、FER、文本一致率和三张结果图。"};
    function stageLabel(name) { return stageNameMap[name] || name; }
    function stageDetail(stage) { return stageDetailMap[stage.name] || stage.detail || ""; }
    const stageLessons = [["Source Encode","UTF-8 bytes -> bits","源编码把文字变成 0/1 比特流。中文、英文和标点先变成 UTF-8 字节，再按位展开。"],["Scramble / Encrypt","b_scrambled = b XOR PN(seed)","扰码使用固定 seed 生成 PN 序列，并与源比特异或；接收端再异或一次即可恢复。"],["Channel Encode","重复码 / 卷积码","信道编码加入冗余。重复码用多数表决，卷积码用 Viterbi 选择最可能的原始比特路径。"],["Frame Build","Preamble | Length | Payload | CRC","帧结构提供同步锚点、原始长度、传输载荷和校验字段。"],["QPSK Modulate","00,01,11,10 -> 星座点","基础模式使用 Gray QPSK；高级模式还支持 BPSK、16-QAM 和按 SNR 自适应选择。"],["OFDM Modulate","IFFT + CP","开启 OFDM 后，调制符号被放到多个子载波上，并添加循环前缀以抵抗多径影响。"],["Wireless Channel","AWGN / Rayleigh / MRC","信道加入噪声或衰落。Rayleigh 模式可用一拍均衡，也可用两分支 MRC 分集。"],["Synchronization","argmax correlation(rx, preamble)","接收端用已知前导做滑动相关，相关峰值对应估计帧起点。"],["OFDM Demodulate","remove CP + FFT","OFDM 接收端移除循环前缀并做 FFT，恢复频域子载波符号。"],["QPSK Demodulate","hard decision","解调根据接收点位置做硬判决，把星座点还原为比特。"],["Channel Decode","majority / Viterbi","译码利用冗余纠错，降低信道噪声带来的比特错误。"],["Descramble / Decrypt","b = b_scrambled XOR PN(seed)","解扰与扰码使用同一个 XOR 运算，只要 seed 一致即可恢复。"],["Source Decode","bits -> UTF-8 text","源解码把恢复后的比特按 8 位拼成字节，再按 UTF-8 还原为文本。"],["Metrics / Plots","BER, FER, match rate, plots","最后生成 BER、FER、文本一致率、校验结果、星座图、BER 曲线和同步峰值图。"]];
    function diagram(title) { return `<svg viewBox="0 0 360 210" role="img"><rect x="24" y="78" width="112" height="58" rx="8" fill="#10262e" stroke="#39d7c8"/><text x="80" y="112" text-anchor="middle" style="font-size:14px;fill:#edf8f7">输入</text><path d="M145 107 L214 107" stroke="#39d7c8" stroke-width="3" marker-end="url(#arrow)"/><rect x="224" y="78" width="112" height="58" rx="8" fill="#0b171d" stroke="#f7b955"/><text x="280" y="112" text-anchor="middle" style="font-size:14px;fill:#edf8f7">${title}</text><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#39d7c8"/></marker></defs></svg>`; }
    function valueText(value) { if (value === true) return "通过"; if (value === false) return "未通过"; if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(4).replace(/0+$/, "").replace(/\.$/, ""); return String(value ?? "--"); }
    function renderDashboard(metrics) { const items = [["BER", metrics.ber, metrics.ber === 0],["FER", metrics.fer, metrics.fer === 0],["文本一致率", metrics.text_match_rate, metrics.text_match_rate === 1],["CRC / Checksum", metrics.checksum_pass, metrics.checksum_pass === true],["同步误差", metrics.sync_error_symbols, metrics.sync_error_symbols === 0],["SNR", metrics.snr_db ?? $("snr").value, true],["调制", metrics.effective_modulation || metrics.modulation || $("mod").value, true],["信道", metrics.channel || $("channel").value, true]]; $("dashboard").innerHTML = items.map(([label,value,good]) => `<div class="metric-card ${good ? "good" : "warn"}"><span>${label}</span><strong>${valueText(value)}</strong></div>`).join(""); const advanced = metrics.ofdm_enabled || metrics.diversity !== "none" || metrics.requested_modulation === "adaptive" || metrics.channel_code === "convolutional-viterbi"; $("modeBadge").textContent = advanced ? "高级模块模式" : "基础验收模式"; }
    function liveChips(stageName) { const stage = latestStages.find((item) => item.name === stageName) || latestStages.find((item) => stageName.includes(item.name) || item.name.includes(stageName)); if (!stage) return '<span>运行后显示实时数值</span>'; return Object.entries(stage).filter(([key,value]) => !traceIgnore.has(key) && value !== null && value !== undefined).map(([key,value]) => `<span>${key}: ${String(value)}</span>`).join(""); }
    function renderLesson(index) { activeLesson = index; const [name, formula, paragraph] = stageLessons[index]; $("stageDiagram").innerHTML = diagram(stageLabel(name)); $("stageTitle").textContent = `${index + 1}. ${stageLabel(name)}`; $("stageText").textContent = paragraph; $("stageFormula").textContent = formula; $("stageLive").innerHTML = liveChips(name); document.querySelectorAll(".flow-step").forEach((button,i) => button.classList.toggle("active", i === index)); }
    function renderFlowSteps() { $("flowSteps").innerHTML = stageLessons.map((lesson,index) => `<button type="button" class="flow-step" data-index="${index}">${index + 1}. ${stageLabel(lesson[0])}</button>`).join(""); document.querySelectorAll(".flow-step").forEach((button) => button.addEventListener("click", () => renderLesson(Number(button.dataset.index)))); renderLesson(activeLesson); }
    function renderTrace(stages) { $("trace").innerHTML = stages.map((stage,index) => { const chips = Object.entries(stage).filter(([key,value]) => !traceIgnore.has(key) && value !== null && value !== undefined).map(([key,value]) => `<span>${key}: ${String(value)}</span>`).join(""); return `<div class="trace-card"><h3>${index + 1}. ${stageLabel(stage.name)}</h3><p>${stageDetail(stage)}</p><div class="kv">${chips}</div></div>`; }).join(""); }
    function escapeHtml(text) { return String(text).replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char])); }
    function writeLog(lines) { $("demoLog").innerHTML = lines.map((line) => `<li>${escapeHtml(line)}</li>`).join(""); }
    function renderDiff(source, received) { if (!source && !received) { $("diffOutput").innerHTML = "运行后显示输入与恢复文本差异。"; return; } if (source === received) { $("diffOutput").innerHTML = "MATCH: 输入文本与 received.txt 完全一致。"; return; } const maxLen = Math.max(source.length, received.length); let output = ""; for (let i = 0; i < maxLen; i += 1) { const a = source[i] ?? ""; const b = received[i] ?? ""; output += a === b ? escapeHtml(a) : `<mark>${escapeHtml(a || "∅")}→${escapeHtml(b || "∅")}</mark>`; } $("diffOutput").innerHTML = output; }
    function syncSnr(value) { const bounded = Math.max(0, Math.min(24, Number(value) || 0)); $("snr").value = bounded; $("snrRange").value = bounded; }
    function setPreset(kind) { const presets = { base: { snr: 12, mod: "qpsk", channel: "awgn", coding: "repetition3", diversity: "none", ofdm: "false", text: "已切换到基础验收参数。" }, advanced: { snr: 24, mod: "adaptive", channel: "rayleigh", coding: "conv", diversity: "mrc2", ofdm: "true", text: "已切换到高级模块参数。" }, low: { snr: 3, mod: "qpsk", channel: "awgn", coding: "none", diversity: "none", ofdm: "false", text: "已切换到低SNR失败演示：观察 BER、CRC 和文本恢复率。" }, rayleigh: { snr: 18, mod: "qpsk", channel: "rayleigh", coding: "repetition3", diversity: "none", ofdm: "false", text: "已切换到 Rayleigh 衰落演示：观察均衡后的星座恢复。" } }; const preset = presets[kind] || presets.base; syncSnr(preset.snr); $("mod").value = preset.mod; $("channel").value = preset.channel; $("coding").value = preset.coding; $("diversity").value = preset.diversity; $("ofdm").value = preset.ofdm; $("scramble").value = "pn-xor"; $("status").textContent = preset.text; writeLog([`[DEMO] ${preset.text}`, `[PARAM] SNR=${preset.snr}dB, mod=${preset.mod}, channel=${preset.channel}, coding=${preset.coding}`]); renderDashboard({text_match_rate: "--", ber: "--", fer: "--", checksum_pass: "--", sync_error_symbols: "--", snr_db: preset.snr, modulation: preset.mod, channel: preset.channel}); }
    document.querySelectorAll(".tab-button").forEach((button) => { button.addEventListener("click", () => { document.querySelectorAll(".tab-button").forEach((item) => item.classList.remove("active")); document.querySelectorAll(".tab-panel").forEach((item) => item.classList.remove("active")); button.classList.add("active"); $(button.dataset.tab).classList.add("active"); }); });
    $("presetBase").addEventListener("click", () => setPreset("base")); $("presetAdvanced").addEventListener("click", () => setPreset("advanced"));
    $("snrRange").addEventListener("input", (event) => syncSnr(event.target.value)); $("snr").addEventListener("input", (event) => syncSnr(event.target.value));
    document.querySelectorAll("[data-demo]").forEach((button) => button.addEventListener("click", () => setPreset(button.dataset.demo === "stable" ? "base" : button.dataset.demo)));
    $("run").addEventListener("click", async () => { $("run").disabled = true; $("status").textContent = "正在运行链路仿真..."; const sourceText = $("text").value; $("sourcePreview").textContent = sourceText; writeLog(["[INFO] Source encoding pending", "[INFO] Frame build / channel / sync running"]); try { const response = await fetch("/api/run", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ text: sourceText, snr: Number($("snr").value), seed: Number($("seed").value), channel: $("channel").value, mod: $("mod").value, source_codec: $("sourceCodec").value, scramble: $("scramble").value, coding: $("coding").value, diversity: $("diversity").value, ofdm: $("ofdm").value === "true" }) }); const data = await response.json(); if (!response.ok) throw new Error(data.error || "仿真失败"); latestStages = data.stage_trace || []; renderDashboard(data.metrics); renderTrace(data.stage_trace || []); renderLesson(activeLesson); $("received").textContent = data.received_text; $("json").textContent = JSON.stringify(data.metrics, null, 2); renderDiff(sourceText, data.received_text); $("constellation").src = data.plots.constellation + "?t=" + Date.now(); $("ber").src = data.plots.ber_curve + "?t=" + Date.now(); $("sync").src = data.plots.sync_peak + "?t=" + Date.now(); const syncStage = latestStages.find((stage) => stage.name === "Synchronization") || {}; writeLog([`[INFO] Source encoding done: ${data.metrics.payload_bits} bits`, `[INFO] Sync found at index ${data.metrics.sync_start_index} (error ${data.metrics.sync_error_symbols})`, `[INFO] BER = ${valueText(data.metrics.ber)}, FER = ${valueText(data.metrics.fer)}`, `[INFO] Text match = ${valueText(data.metrics.text_match_rate)}, CRC = ${valueText(data.metrics.checksum_pass)}`, `[INFO] Peak value = ${valueText(syncStage.peak_value)}`]); $("status").textContent = "仿真完成，结果已刷新。"; } catch (error) { $("status").textContent = error.message; writeLog([`[ERROR] ${error.message}`]); } finally { $("run").disabled = false; } });
    renderDashboard({text_match_rate: "--", ber: "--", fer: "--", checksum_pass: "--", sync_error_symbols: "--", snr_db: 12, modulation: "qpsk", channel: "awgn"}); renderFlowSteps(); $("sourcePreview").textContent = $("text").value;
  </script>
</body>
</html>
"""


class WirelessRequestHandler(BaseHTTPRequestHandler):
    server: "WirelessHTTPServer"

    def log_message(self, fmt: str, *args) -> None:
        return

    def _send_bytes(self, body: bytes, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        self._send_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"), status, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_bytes(INDEX_HTML.encode("utf-8"), content_type="text/html; charset=utf-8")
            return
        if parsed.path.startswith("/results/"):
            relative = unquote(parsed.path.removeprefix("/results/"))
            target = (self.server.base_dir / "results" / relative).resolve()
            results_root = (self.server.base_dir / "results").resolve()
            if not str(target).startswith(str(results_root)) or not target.exists() or not target.is_file():
                self._send_json({"error": "result file not found"}, HTTPStatus.NOT_FOUND)
                return
            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            self._send_bytes(target.read_bytes(), content_type=content_type)
            return
        self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/run":
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            text = str(payload.get("text", ""))
            if not text.strip():
                self._send_json({"error": "发送文本不能为空"}, HTTPStatus.BAD_REQUEST)
                return
            input_path = self.server.base_dir / "web_input.txt"
            output_path = self.server.base_dir / "results" / "received.txt"
            input_path.write_text(text, encoding="utf-8")
            metrics = run_pipeline(input_path, output_path, snr_db=float(payload.get("snr", 12)), seed=int(payload.get("seed", 2026)), modulation=str(payload.get("mod", "qpsk")).lower(), channel_name=str(payload.get("channel", "awgn")).lower(), source_codec=str(payload.get("source_codec", "utf8")).lower(), scramble_mode=str(payload.get("scramble", "pn-xor")).lower(), coding_mode=str(payload.get("coding", "repetition3")).lower(), diversity=str(payload.get("diversity", "none")).lower(), ofdm_enabled=bool(payload.get("ofdm", False)))
            response = {"metrics": metrics, "stage_trace": metrics.get("stage_trace", []), "received_text": output_path.read_text(encoding="utf-8"), "plots": {"constellation": "/results/constellation.png", "ber_curve": "/results/ber_curve.png", "sync_peak": "/results/sync_peak.png"}}
            self._send_json(response)
        except Exception as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)


class WirelessHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address, RequestHandlerClass, base_dir: Path):
        super().__init__(server_address, RequestHandlerClass)
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "results").mkdir(parents=True, exist_ok=True)


def create_app_server(host: str = "127.0.0.1", port: int = 8000, base_dir: str | Path | None = None) -> WirelessHTTPServer:
    return WirelessHTTPServer((host, port), WirelessRequestHandler, Path(base_dir or ".").resolve())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local web UI for the wireless baseband simulator")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--base-dir", default=".")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = create_app_server(args.host, args.port, args.base_dir)
    host, port = server.server_address
    print(f"Web simulator running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
