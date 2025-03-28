from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from typing import Optional
from .settings import ApplicationSettings

app = FastAPI()

class ProxyServer:
    def __init__(self, settings: ApplicationSettings):
        self.settings = settings
        self._initialize_backend_urls()

    def _initialize_backend_urls(self):
        """バックエンドサーバーのURLを初期化"""
        self.backend_urls = {
            service.name: f"http://localhost:{service.port}"
            for service in self.settings.services
        }

    def _get_target_service(self, path: str):
        """パスに基づいて適切なバックエンドサービスを選択"""
        # 現在は最初のサービスを使用
        # TODO: パスに基づいてサービスを選択するロジックを実装
        return self.settings.services[0]

    async def forward_request(self, request: Request, path: str) -> StreamingResponse:
        """リクエストをバックエンドサーバーに転送し、レスポンスを返却する"""
        try:
            service = self._get_target_service(path)
            target_url = f"{self.backend_urls[service.name]}/{path}"

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
            raise HTTPException(status_code=504, detail="ゲートウェイタイムアウト")
        except httpx.ConnectError:
            raise HTTPException(status_code=502, detail="バックエンドサーバーに接続できません")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"内部サーバーエラー: {str(e)}")

# シングルトンインスタンス
_proxy_server: Optional[ProxyServer] = None

def get_proxy_server() -> Optional[ProxyServer]:
    """プロキシサーバーインスタンスを取得"""
    return _proxy_server

def init_proxy(settings: ApplicationSettings):
    """プロキシサーバーの初期化"""
    global _proxy_server
    _proxy_server = ProxyServer(settings)

@app.post("/{path:path}")
@app.get("/{path:path}")
async def proxy_endpoint(request: Request, path: str):
    """全てのリクエストを受け付けるエンドポイント"""
    proxy_server = get_proxy_server()
    if not proxy_server:
        raise HTTPException(status_code=500, detail="プロキシサーバーが初期化されていません")

    return await proxy_server.forward_request(request, path) 