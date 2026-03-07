import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

class BlenderBridgeClient:
    """
    Client for interacting with the Blender UI thread over HTTP.
    Extremely resilient, automatically retries on timeout, safely handles stale bridge port states.
    """
    def __init__(self, lock_file_path: Path):
        self.lock_file = lock_file_path

    def _get_credentials(self) -> Optional[Dict[str, str]]:
        if not self.lock_file.exists():
            return None
        try:
            # Check for stale lockfile (>24 hours) as an edge-case warning
            import time
            if time.time() - self.lock_file.stat().st_mtime > 86400:
                logger.warning("Blender lockfile is older than 24 hours. Connect might fail if Blender restarted.")
                
            with open(self.lock_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to parse lockfile credentials: {e}")
            return None

    # Exponential backoff targeting connection errors and UI thread timeouts
    @retry(
        wait=wait_exponential(multiplier=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException))
    )
    async def request(self, endpoint: str, payload: dict = None) -> Dict[str, Any]:
        creds = self._get_credentials()
        if not creds:
            return {"status": "error", "message": "Elite MCP Bridge is completely disconnected. Launch blender plugin."}
            
        port = creds.get("port")
        token = creds.get("token")
        
        # Default timeouts: HTTP Connect gets 5s, Read pool gets 40s (Allows for heavy Python executions or rendering)
        timeout_config = httpx.Timeout(120.0, connect=5.0)
        
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            url = f"http://127.0.0.1:{port}{endpoint}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            try:
                if payload:
                    response = await client.post(url, headers=headers, json=payload)
                else:
                    response = await client.get(url, headers=headers)
                    
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                # HTTP specific errors (e.g. 403 Forbidden on bad tokens)
                return {"status": "error", "message": f"Bridge Server rejected payload. Status {e.response.status_code}"}
            except httpx.RequestError as e:
                # Surface error for Tenacity to retry!
                logger.warning(f"Connection glitch pinging Blender UI thread: {e}. Retrying.")
                raise e
            except Exception as e:
                return {"status": "error", "message": f"Critical parsing failure inside HTTP payload: {e}"}
