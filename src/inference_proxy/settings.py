from pathlib import Path
from typing import List, Any
import os
import yaml
from pydantic import BaseModel, Field, field_validator, ValidationInfo

class ServiceSettings(BaseModel):
    """サービス設定モデル"""
    name: str = Field(..., min_length=1, description="サービス名")
    image: str = Field(..., min_length=1, description="Dockerイメージ名")
    port: int = Field(..., gt=0, lt=65536, description="サービスのポート番号")

class LogSettings(BaseModel):
    """ログ設定モデル"""
    output_dir: Path = Field(..., description="ログ出力ディレクトリ")
    level: str = Field("INFO", description="ログレベル")

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v not in valid_levels:
            raise ValueError(f"ログレベルは以下のいずれかである必要があります: {', '.join(valid_levels)}")
        return v

    @field_validator("output_dir", mode="before")
    @classmethod
    def validate_output_dir(cls, v: Any) -> Any:
        if v == "":
            raise ValueError("出力ディレクトリを指定する必要があります")
        return v

class ApplicationSettings(BaseModel):
    """アプリケーション全体の設定モデル"""
    services: List[ServiceSettings] = Field(..., min_length=1, description="サービス設定のリスト")
    logging: LogSettings = Field(..., description="ログ設定")

def load_settings(config_path: Path) -> ApplicationSettings:
    """
    YAMLファイルから設定を読み込み、環境変数でオーバーライドする
    
    Args:
        config_path: 設定ファイルのパス
        
    Returns:
        ApplicationSettings: 読み込んだ設定
        
    Raises:
        FileNotFoundError: 設定ファイルが存在しない場合
        ValidationError: 設定値が無効な場合
    """
    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

    with open(config_path) as f:
        config_data = yaml.safe_load(f)

    # 環境変数によるオーバーライド
    if "AI_PROXY_SERVICE_PORT" in os.environ:
        port = int(os.environ["AI_PROXY_SERVICE_PORT"])
        for service in config_data.get("services", []):
            service["port"] = port

    if "AI_PROXY_LOG_LEVEL" in os.environ:
        config_data["logging"]["level"] = os.environ["AI_PROXY_LOG_LEVEL"]

    return ApplicationSettings(**config_data)