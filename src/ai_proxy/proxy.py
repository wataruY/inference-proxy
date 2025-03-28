from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from typing import Optional
from .settings import Settings

app = FastAPI()
client = httpx.AsyncClient()

class ProxyServer:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def forward_request(self, request: Request, target_url: str) -> StreamingResponse:
        """リクエストをバックエンドサーバーに転送し、レスポンスを返却する"""
        try:
            # リクエストヘッダーとボディの取得
            headers = dict(request.headers)
            body = await request.body()

            # バックエンドサーバーへのリクエスト
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                    timeout=30.0  # タイムアウトの設定
                )

            # レスポンスの返却
            return StreamingResponse(
                content=response.aiter_raw(),
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Gateway Timeout")
        except httpx.ConnectError:
            raise HTTPException(status_code=502, detail="Bad Gateway")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

proxy_server: Optional[ProxyServer] = None

def init_proxy(settings: Settings):
    """プロキシサーバーの初期化"""
    global proxy_server
    proxy_server = ProxyServer(settings)

@app.post("/{path:path}")
@app.get("/{path:path}")
async def proxy_endpoint(request: Request, path: str):
    """全てのリクエストを受け付けるエンドポイント"""
    if not proxy_server:
        raise HTTPException(status_code=500, detail="Proxy server not initialized")

    # TODO: バックエンドサーバーのURLを設定から取得する
    target_url = f"http://localhost:8000/{path}"
    return await proxy_server.forward_request(request, target_url) 