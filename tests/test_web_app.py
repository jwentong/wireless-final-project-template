import json
import threading
import urllib.error
import urllib.request

from web_app import create_app_server


def test_web_home_page_contains_simulator_controls(tmp_path):
    server = create_app_server(host="127.0.0.1", port=0, base_dir=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/"
        html = urllib.request.urlopen(url, timeout=5).read().decode("utf-8")
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert "无线通信基带仿真系统" in html
    assert "发射机控制台" in html
    assert "接收机观测窗" in html
    assert "实验室链路" in html
    assert "scope-grid" in html
    assert "突出结果图" in html
    assert "一键基础验收" in html
    assert "一键高级模块" in html
    assert "主图：接收星座图" in html
    assert "OFDM" in html
    assert "2 分支 MRC" in html
    assert "snr" in html.lower()
    assert "channel" in html.lower()
    assert "chainTab" in html
    assert "stageDiagram" in html
    assert "stageText" in html
    assert "stageLive" in html
    assert "const stageLessons" in html
    assert "SNR滑块" in html
    assert "12dB稳定通信演示" in html
    assert "低SNR失败演示" in html
    assert "Rayleigh衰落演示" in html
    assert "实时日志" in html
    assert "文本对比" in html
    assert "方案对比" in html
    assert "demoLog" in html
    assert "diffOutput" in html
    assert "信号证据板" in html
    assert "星座聚类" in html
    assert "误码率下降" in html
    assert "同步峰值锁定" in html
    assert "源码阶段名称映射" in html
    assert "source_stage_name" in html


def test_web_api_runs_pipeline_and_returns_metrics(tmp_path):
    server = create_app_server(host="127.0.0.1", port=0, base_dir=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/api/run"
        payload = json.dumps(
            {
                "text": "Web 仿真接口测试。",
                "snr": 12,
                "seed": 2026,
                "channel": "awgn",
                "source_codec": "utf8",
                "scramble": "pn-xor",
                "coding": "repetition3",
            }
        ).encode("utf-8")
        request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        body = urllib.request.urlopen(request, timeout=20).read().decode("utf-8")
    finally:
        server.shutdown()
        thread.join(timeout=5)

    data = json.loads(body)
    assert data["metrics"]["text_match_rate"] == 1.0
    assert data["metrics"]["checksum_pass"] is True
    assert data["received_text"] == "Web 仿真接口测试。"
    assert "constellation.png" in data["plots"]["constellation"]
    assert [stage["name"] for stage in data["stage_trace"]] == [
        "Source Encode",
        "Scramble / Encrypt",
        "Channel Encode",
        "Frame Build",
        "QPSK Modulate",
        "Wireless Channel",
        "Synchronization",
        "QPSK Demodulate",
        "Channel Decode",
        "Descramble / Decrypt",
        "Source Decode",
        "Metrics / Plots",
    ]


def test_web_api_allows_advanced_module_options(tmp_path):
    server = create_app_server(host="127.0.0.1", port=0, base_dir=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/api/run"
        payload = json.dumps(
            {
                "text": "Advanced web option demo.",
                "snr": 24,
                "seed": 2026,
                "channel": "rayleigh",
                "mod": "adaptive",
                "scramble": "pn-xor",
                "coding": "conv",
                "diversity": "mrc2",
                "ofdm": True,
            }
        ).encode("utf-8")
        request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        body = urllib.request.urlopen(request, timeout=20).read().decode("utf-8")
    finally:
        server.shutdown()
        thread.join(timeout=5)

    data = json.loads(body)
    assert data["received_text"] == "Advanced web option demo."
    assert data["metrics"]["requested_modulation"] == "adaptive"
    assert data["metrics"]["channel_code"] == "convolutional-viterbi"
    assert data["metrics"]["diversity"] == "mrc2"
    assert data["metrics"]["ofdm_enabled"] is True


def test_web_api_allows_no_scramble_no_coding_demo_mode(tmp_path):
    server = create_app_server(host="127.0.0.1", port=0, base_dir=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/api/run"
        payload = json.dumps(
            {
                "text": "Module option demo.",
                "snr": 20,
                "seed": 2026,
                "channel": "awgn",
                "scramble": "none",
                "coding": "none",
            }
        ).encode("utf-8")
        request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        body = urllib.request.urlopen(request, timeout=20).read().decode("utf-8")
    finally:
        server.shutdown()
        thread.join(timeout=5)

    data = json.loads(body)
    assert data["received_text"] == "Module option demo."
    assert data["metrics"]["scrambler"] == "none"
    assert data["metrics"]["channel_code"] == "none"


def test_web_api_rejects_empty_text(tmp_path):
    server = create_app_server(host="127.0.0.1", port=0, base_dir=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/api/run"
        request = urllib.request.Request(
            url,
            data=json.dumps({"text": ""}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(request, timeout=5)
            assert False, "empty text should return HTTP 400"
        except urllib.error.HTTPError as exc:
            assert exc.code == 400
    finally:
        server.shutdown()
        thread.join(timeout=5)
