"""
Module giao tiếp với ComfyUI API.
Upload ảnh, build prompt, queue job, listen progress, lấy output.
"""

import json
import random
import asyncio
import logging
from datetime import datetime

import httpx
import websockets

from config import WORKFLOW_PATH, WORKFLOW_DEFAULTS

logger = logging.getLogger("comfyui_client")


# ── Health check ────────────────────────────────────────────


async def check_server(server_url: str, timeout: float = 5) -> bool:
    """Kiểm tra ComfyUI server có online không."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(f"{server_url}/system_stats")
            return r.status_code == 200
    except Exception:
        return False


# ── Upload ảnh ──────────────────────────────────────────────


async def upload_image(server_url: str, image_path: str, filename: str) -> str:
    """Upload ảnh lên ComfyUI, trả về tên file trên server."""
    async with httpx.AsyncClient(timeout=60) as client:
        with open(image_path, "rb") as f:
            r = await client.post(
                f"{server_url}/upload/image",
                files={"image": (filename, f, "image/jpeg")},
                data={"overwrite": "true"},
            )
            r.raise_for_status()
            result = r.json()
            logger.info(f"Uploaded {filename} → ComfyUI: {result['name']}")
            return result["name"]


# ── Workflow builder ────────────────────────────────────────


def build_prompt(image_name: str, seed: int | None = None) -> dict:
    """
    Load workflow JSON và patch input nodes.
    Chỉ thay đổi: image, seed, filename_prefix.
    Resolution/frames/prompt giữ cố định.
    """
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        prompt = json.load(f)

    # ── Ảnh input (node 146 - LoadImage)
    prompt["146"]["inputs"]["image"] = image_name

    # ── Resolution + frames (node 169)
    prompt["169"]["inputs"]["width"] = WORKFLOW_DEFAULTS["width"]
    prompt["169"]["inputs"]["height"] = WORKFLOW_DEFAULTS["height"]
    prompt["169"]["inputs"]["length"] = WORKFLOW_DEFAULTS["length"]

    # ── Random seed (node 57 + 58 - KSamplerAdvanced)
    if seed is None:
        seed = random.randint(0, 2**53)
    prompt["57"]["inputs"]["noise_seed"] = seed
    prompt["58"]["inputs"]["noise_seed"] = seed + 1

    # ── Output filename prefix
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    prompt["82"]["inputs"]["filename_prefix"] = f"{date_prefix}\\wan22"

    return prompt


# ── Queue prompt ────────────────────────────────────────────


async def queue_prompt(server_url: str, prompt: dict, client_id: str) -> str:
    """Submit prompt vào ComfyUI queue, trả về prompt_id."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{server_url}/prompt",
            json={"prompt": prompt, "client_id": client_id},
        )
        r.raise_for_status()
        prompt_id = r.json()["prompt_id"]
        logger.info(f"Queued prompt {prompt_id}")
        return prompt_id


# ── WebSocket progress listener ────────────────────────────


async def listen_progress(
    server_url: str,
    prompt_id: str,
    client_id: str,
    on_progress=None,
    timeout_s: int = 900,
) -> dict:
    """
    Lắng nghe WebSocket ComfyUI để theo dõi tiến độ job.
    Trả về {"status": "done"} hoặc {"status": "error", "error": "..."}.

    Xử lý cả trường hợp:
    - progress messages (KSampler nodes)
    - executing messages (tất cả nodes, done khi node=None)
    - executed messages (node hoàn thành)
    - execution_cached (node đã cached)
    - binary data (preview frames từ VHS)
    """
    ws_url = server_url.replace("http://", "ws://").replace("https://", "wss://")
    ws_url = f"{ws_url}/ws?clientId={client_id}"

    # Tổng số node trong workflow để tính progress phụ
    TOTAL_NODES = 16  # 16 nodes trong FULLHD_6S_Loop_API.json
    executed_nodes = set()
    last_progress_pct = 0

    try:
        async with websockets.connect(
            ws_url,
            ping_interval=30,
            ping_timeout=120,
            max_size=50 * 1024 * 1024,  # 50MB cho binary frames
            close_timeout=10,
        ) as ws:
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=timeout_s)
                except asyncio.TimeoutError:
                    # Timeout — thử check history trước khi báo lỗi
                    logger.warning(f"WS timeout {timeout_s}s, checking history...")
                    try:
                        hist = await get_history(server_url, prompt_id)
                        if prompt_id in hist:
                            status = hist[prompt_id].get("status", {})
                            if status.get("completed", False):
                                logger.info("Job completed (detected via history)")
                                return {"status": "done"}
                    except Exception:
                        pass
                    raise TimeoutError(f"Job timeout sau {timeout_s}s")

                if isinstance(msg, bytes):
                    # Binary data = preview hoặc video frame
                    # VHS_VideoCombine có thể gửi nhiều binary frames
                    logger.debug(f"Binary frame: {len(msg)} bytes")
                    continue

                data = json.loads(msg)
                msg_type = data.get("type", "")
                msg_data = data.get("data", {})

                logger.debug(f"WS msg: {msg_type} | {json.dumps(msg_data)[:200]}")

                if msg_type == "progress":
                    # KSampler progress — chiếm ~85% tổng thời gian
                    value = msg_data.get("value", 0)
                    max_val = msg_data.get("max", 1)
                    # Scale progress: KSampler = 0-85%
                    raw_pct = (value / max_val) if max_val > 0 else 0
                    pct = int(raw_pct * 85)
                    if pct > last_progress_pct:
                        last_progress_pct = pct
                        if on_progress:
                            await on_progress(pct)

                elif msg_type == "executing":
                    node = msg_data.get("node")
                    pid = msg_data.get("prompt_id")

                    # node=None nghĩa là prompt execution kết thúc
                    if node is None:
                        # Chỉ quan tâm đến prompt của mình
                        if pid == prompt_id:
                            logger.info(
                                f"Job {prompt_id[:8]}… executing done (node=None)"
                            )
                            if on_progress:
                                await on_progress(100)
                            return {"status": "done"}
                        else:
                            # Prompt khác kết thúc — bỏ qua
                            continue
                    else:
                        # Node đang chạy — cập nhật progress dựa trên node
                        if pid == prompt_id:
                            logger.info(f"Executing node: {node}")

                elif msg_type == "executed":
                    # Node hoàn thành — dùng để tính progress phụ
                    pid = msg_data.get("prompt_id")
                    node = msg_data.get("node")
                    if pid == prompt_id and node:
                        executed_nodes.add(node)
                        # Progress phụ: 85% + (executed_nodes / TOTAL) * 15%
                        extra = int((len(executed_nodes) / TOTAL_NODES) * 15)
                        pct = min(85 + extra, 99)
                        if pct > last_progress_pct:
                            last_progress_pct = pct
                            if on_progress:
                                await on_progress(pct)

                elif msg_type == "execution_cached":
                    # Nodes đã cached — cũng tính vào progress
                    pid = msg_data.get("prompt_id")
                    nodes = msg_data.get("nodes", [])
                    if pid == prompt_id:
                        for n in nodes:
                            executed_nodes.add(n)

                elif msg_type == "execution_error":
                    error = msg_data.get("exception_message", "Unknown error")
                    traceback_info = msg_data.get("traceback", "")
                    logger.error(f"Execution error: {error}\n{traceback_info[:500]}")
                    return {"status": "error", "error": error}

                elif msg_type == "execution_interrupted":
                    return {"status": "error", "error": "Job bị hủy"}

                elif msg_type == "status":
                    # Queue status update — có thể dùng để detect idle
                    queue_remaining = (
                        msg_data.get("status", {})
                        .get("exec_info", {})
                        .get("queue_remaining", -1)
                    )
                    logger.debug(f"Queue remaining: {queue_remaining}")

    except websockets.ConnectionClosed as e:
        # WS đóng — check history xem job đã xong chưa
        logger.warning(f"WS closed: {e}, checking history fallback...")
        try:
            await asyncio.sleep(2)  # đợi ComfyUI flush output
            hist = await get_history(server_url, prompt_id)
            if prompt_id in hist:
                outputs = hist[prompt_id].get("outputs", {})
                if outputs:
                    logger.info("Job completed (detected via history after WS close)")
                    if on_progress:
                        await on_progress(100)
                    return {"status": "done"}
        except Exception as he:
            logger.error(f"History fallback failed: {he}")

        raise ConnectionError(f"Mất kết nối WS ComfyUI: {e}")


# ── History / Output ────────────────────────────────────────


async def get_history(server_url: str, prompt_id: str) -> dict:
    """Lấy history output sau khi prompt chạy xong."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{server_url}/history/{prompt_id}")
        r.raise_for_status()
        return r.json()


def extract_output_info(history: dict, prompt_id: str) -> dict | None:
    """Trích xuất thông tin video output từ ComfyUI history."""
    if prompt_id not in history:
        return None

    outputs = history[prompt_id].get("outputs", {})

    # Node 82 — VHS_VideoCombine output
    if "82" in outputs:
        node_out = outputs["82"]

        # VHS có thể dùng "gifs" hoặc "videos" key
        for key in ("gifs", "videos", "images"):
            items = node_out.get(key, [])
            if items:
                return {
                    "filename": items[0]["filename"],
                    "subfolder": items[0].get("subfolder", ""),
                    "type": items[0].get("type", "output"),
                }

    # Fallback: tìm bất kỳ node nào có output video/gif
    for node_id, node_out in outputs.items():
        for key in ("gifs", "videos"):
            items = node_out.get(key, [])
            if items:
                return {
                    "filename": items[0]["filename"],
                    "subfolder": items[0].get("subfolder", ""),
                    "type": items[0].get("type", "output"),
                }

    return None


async def download_output(server_url: str, output_info: dict) -> bytes:
    """Download video output từ ComfyUI server."""
    params = {
        "filename": output_info["filename"],
        "subfolder": output_info.get("subfolder", ""),
        "type": output_info.get("type", "output"),
    }
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.get(f"{server_url}/view", params=params)
        r.raise_for_status()
        return r.content
