import rich_click as click
from rich_click import RichCommand, RichGroup
import docker
from docker.client import DockerClient
from docker.models.containers import Container

@click.group(cls=RichGroup)
def cli():
    pass

@cli.command(cls=RichCommand)
@click.option("--name", type=str, default="World")
@click.option("--age", type=int, default=0)
def main(name: str, age: int):
    click.echo(f"Hello {name}!")
    click.echo(f"You are {age} years old!")

@cli.command(cls=RichCommand, name="docker")
def run_test_docker_container():
    """
    run container and wait for it to finish.
    print logs.
    """
    client: DockerClient = docker.from_env()
    
    # テスト用のコンテナを実行
    container: Container = client.containers.run(
        "hello-world",  # テスト用の軽量なイメージ
        detach=True     # バックグラウンドで実行
    )
    
    try:
        # コンテナの完了を待つ
        container.wait()
        
        # ログを出力
        logs = container.logs().decode('utf-8')
        click.echo(logs)
    finally:
        # 最後にコンテナを削除
        container.remove(force=True)

if __name__ == "__main__":
    cli()
    
