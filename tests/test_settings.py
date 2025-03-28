import pytest
from pathlib import Path
from pydantic import ValidationError
from inference_proxy.settings import (
    ServiceSettings,
    LogSettings,
    ApplicationSettings,
    load_settings
)

def test_service_settings_validation():
    """サービス設定のバリデーションテスト"""
    valid_settings = {
        "name": "test-service",
        "image": "test-image:latest",
        "port": 8000
    }
    service = ServiceSettings(**valid_settings)
    assert service.name == "test-service"
    assert service.image == "test-image:latest"
    assert service.port == 8000

    # 無効な設定のテスト
    with pytest.raises(ValidationError):
        ServiceSettings(name="", image="test:latest", port=8000)
    with pytest.raises(ValidationError):
        ServiceSettings(name="test", image="", port=8000)
    with pytest.raises(ValidationError):
        ServiceSettings(name="test", image="test:latest", port=-1)

def test_log_settings_validation():
    """ログ設定のバリデーションテスト"""
    valid_settings = {
        "output_dir": "/var/log",
        "level": "INFO"
    }
    log_settings = LogSettings(**valid_settings)
    assert log_settings.output_dir == Path("/var/log")
    assert log_settings.level == "INFO"

    # 無効な設定のテスト
    with pytest.raises(ValidationError):
        LogSettings(output_dir="", level="INFO")  # 空の出力ディレクトリ
    
    with pytest.raises(ValidationError):
        LogSettings(output_dir="/var/log", level="INVALID")  # 無効なログレベル

def test_application_settings_validation():
    """アプリケーション全体の設定のバリデーションテスト"""
    valid_settings = {
        "services": [{
            "name": "test-service",
            "image": "test-image:latest",
            "port": 8000
        }],
        "logging": {
            "output_dir": "/var/log",
            "level": "INFO"
        }
    }
    app_settings = ApplicationSettings(**valid_settings)
    assert len(app_settings.services) == 1
    assert app_settings.services[0].name == "test-service"
    assert app_settings.logging.level == "INFO"

def test_load_settings_from_yaml(tmp_path):
    """YAMLファイルからの設定読み込みテスト"""
    config_path = tmp_path / "config.yaml"
    config_content = """
    services:
      - name: test-service
        image: test-image:latest
        port: 8000
    logging:
      output_dir: /var/log
      level: INFO
    """
    config_path.write_text(config_content)

    settings = load_settings(config_path)
    assert len(settings.services) == 1
    assert settings.services[0].name == "test-service"
    assert settings.logging.level == "INFO"

def test_load_settings_with_env_override(tmp_path, monkeypatch):
    """環境変数によるオーバーライドのテスト"""
    config_path = tmp_path / "config.yaml"
    config_content = """
    services:
      - name: test-service
        image: test-image:latest
        port: 8000
    logging:
      output_dir: /var/log
      level: INFO
    """
    config_path.write_text(config_content)

    monkeypatch.setenv("AI_PROXY_SERVICE_PORT", "9000")
    monkeypatch.setenv("AI_PROXY_LOG_LEVEL", "DEBUG")

    settings = load_settings(config_path)
    assert settings.services[0].port == 9000
    assert settings.logging.level == "DEBUG" 