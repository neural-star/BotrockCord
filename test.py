import argparse
import json
import shutil
from pathlib import Path
import uuid

def enable_addon(
    world_path: Path,
    addon_path: Path,
    pack_type: str  # "behavior_packs" or "resource_packs"
):
    """
    world_path: ワールドフォルダへのパス
    addon_path: 有効化したいアドオンフォルダへのパス（内部に manifest.json があること）
    pack_type: "behavior_packs" か "resource_packs"
    """

    # 1) アドオンの manifest.json を読む
    manifest_file = addon_path / "manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"manifest.json が見つかりません: {manifest_file}")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    header = manifest.get("header")
    if not header:
        raise ValueError("manifest.json に header がありません")

    pack_entry = {
        "pack_id": header.get("uuid", str(uuid.uuid4())),
        "version": header.get("version", [1, 0, 0])
    }

    # 2) ワールド側の settings ファイルを開く（なければ新規作成）
    settings_file = world_path / f"{pack_type}.json"
    if settings_file.exists():
        world_settings = json.loads(settings_file.read_text(encoding="utf-8"))
    else:
        world_settings = {"format_version": 1, "header": {}, pack_type: []}

    # 3) 既存エントリに重複がないか確認
    existing = world_settings.get(pack_type, [])
    if any(e.get("pack_id") == pack_entry["pack_id"] for e in existing):
        print(f"⚠️ このアドオンはすでに有効化されています: {pack_entry['pack_id']}")
    else:
        existing.append(pack_entry)
        world_settings[pack_type] = existing

        # 4) settings ファイルを書き出し
        settings_file.write_text(
            json.dumps(world_settings, ensure_ascii=False, indent=4),
            encoding="utf-8"
        )
        print(f"✅ {pack_type} にアドオンを追加しました: {pack_entry['pack_id']}")

    # 5) アドオンフォルダをワールド内にコピー（上書き可）
    dest_dir = world_path / pack_type / addon_path.name
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(addon_path, dest_dir)
    print(f"🎉 アドオンフォルダをコピーしました: {dest_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Minecraft 統合版ワールドにアドオンを有効化するスクリプト"
    )
    parser.add_argument(
        "--world",
        type=str,
        required=True,
        help="ワールドフォルダへのパス（例: C:/Users/You/AppData/.../minecraftWorlds/xxxxx）"
    )
    parser.add_argument(
        "--addon",
        type=str,
        required=True,
        help="有効化したいアドオンフォルダへのパス"
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["behavior_packs", "resource_packs"],
        default="behavior_packs",
        help="behavior_packs か resource_packs"
    )
    args = parser.parse_args()

    world_path = Path(args.world)
    addon_path = Path(args.addon)

    if not world_path.exists() or not world_path.is_dir():
        print(f"❌ ワールドフォルダが見つかりません: {world_path}")
        return
    if not addon_path.exists() or not addon_path.is_dir():
        print(f"❌ アドオンフォルダが見つかりません: {addon_path}")
        return

    enable_addon(world_path, addon_path, args.type)


if __name__ == "__main__":
    main()
