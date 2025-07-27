import datetime
import zipfile
import shutil
import json
import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ui import Button, View
import yaml

TOKEN = ""

ADMIN = None
USER_IDs = [ADMIN]
CHECK = True
BASE_PATH = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Packages\\Microsoft.MinecraftUWP_8wekyb3d8bbwe\\LocalState\\games\\com.mojang\\minecraftWorlds"
world_path = None
OVERWRITE = False
TIMEOUT = 300

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"✅ ログイン成功: {client.user}")
    await tree.sync()
    print("🌐 スラッシュコマンドを同期しました")
    
class CheckButton(View):
    def __init__(self, file: discord.Attachment):
        super().__init__(timeout=TIMEOUT)
        self.file = file

    @discord.ui.button(label="承認", style=discord.ButtonStyle.green)
    async def add_button(self, interaction: discord.Interaction, button: Button):
        button.disabled = True
        await add_addon(interaction, self.file, alert=False)
        await interaction.followup.send(f"✅ {self.file.filename} を追加しました", ephemeral=True)
        self.stop()

    @discord.ui.button(label="承認しない", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        button.disabled = True
        await interaction.response.send_message("❌ アドオンの追加をキャンセルしました", ephemeral=True)
        self.stop()

def manifest(path):
    manifest_path = os.path.join(path, "manifest.json")
    if not os.path.exists(manifest_path):
        return
    
    with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    
    header = data["header"]
    type = data["modules"][0]["type"]

    if type == "data":
        type = "behaviors"
    elif type != "resources":
        return
    json_path = os.path.join(world_path, f"world_{type[:-1]}_packs.json")
    
    with open(json_path, "r") as f:
        data = json.load(f)
    
    data.append({"pack_id": header["uuid"], "version": header["version"]})
    
    with open(json_path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return (type, header["uuid"])

async def add_addon(interaction: discord.Interaction,file: discord.Attachment, alert: bool = True):
    await interaction.response.defer(thinking=True)
    await file.save(file.filename)
    addon = Path(file.filename)
    #os.startfile(addon)
    
    info = []
    new_path = addon.with_name(addon.stem + ".zip")
    os.rename(addon, new_path)
    if os.path.exists("path"):
        shutil.rmtree("tmp")
    
    with zipfile.ZipFile(new_path, "r") as zip_ref:
        zip_ref.extractall("tmp")
    
    info.append(manifest("tmp"))
    for sub in os.listdir("tmp"):
        sub_path = os.path.join("tmp", sub)
        info.append(manifest(sub_path))
        
    shutil.rmtree("tmp")
    os.remove(new_path)
    
    await interaction.followup.send("✅ アドオンの追加が完了しました！", ephemeral=True)
    with open("ADDON_INFO.json", "r") as f:

@tree.command(name="setup", description="サーバーをセットアップします")
async def setup(interaction: discord.Interaction,
                name: str | None = None,
                overwrite: bool | None= None,
                admin: discord.User | None = None,
                check: bool | None = None,
                add_user: discord.User | None = None,
                del_user: discord.User | None = None,
                timeout: int | None = None):
    global world_path, OVERWRITE, ADMIN, CHECK, USER_IDs, TIMEOUT
    if interaction.user.id not in USER_IDs:
        await interaction.response.send_message("❌ このコマンドを使用できる権限がありません", ephemeral=True)
        return

    if name:
        world_path = os.path.join(BASE_PATH, name)
    if overwrite:
        OVERWRITE = overwrite
    if admin:
        ADMIN = admin.id
    if check:
        CHECK = check
    if add_user:
        USER_IDs.append(add_user.id)
    if del_user:
        if del_user.id in USER_IDs:
            USER_IDs.remove(del_user.id)
    if timeout:
        TIMEOUT = timeout
    
    await interaction.response.send_message("セットアップが完了しました", ephemeral=True)

@tree.command(name="debug", description="デバッグ情報を表示します")
async def debug(interaction: discord.Interaction):
    message = (
        f"name: {os.path.basename(world_path)}\n"
        f"check: {CHECK}\n"
        f"overwrite: {OVERWRITE}\n"
        f"admin: {ADMIN}\n"
        f"users: {USER_IDs}\n"
        f"timeout: {TIMEOUT}\n"
        f"Behavior_List: {os.listdir(os.path.join(world_path, 'behavior_packs'))}\n"
        f"Resource_List: {os.listdir(os.path.join(world_path, 'resource_packs'))}"
    )

    await interaction.response.send_message(message, ephemeral=True)

@tree.command(name="del_addon", description="サーバーからアドオンを削除します")
async def del_addon(interaction: discord.Interaction, name: str):
    if not world_path:
        await interaction.response.send_message("❌ ワールドが設定されていません。`/setup`コマンドでワールドを設定してください", ephemeral=True)
        return
    
    

@tree.command(name="addon", description="サーバーにアドオンを追加します")
async def addon(interaction: discord.Interaction, file: discord.Attachment):
    name = file.filename
    if not name.endswith((".mcaddon", ".mcpack")):
        await interaction.response.send_message(
            "❌ 無効なファイル形式です。`.mcaddon, .mcpack`のどちらかの拡張子のファイルをアップロードしてください",
            ephemeral=True
        )
        return

    if CHECK and interaction.user.id != ADMIN:
        view = CheckButton(file)
        user = await client.fetch_user(ADMIN)
        await interaction.response.send_message(f"{user.mention}\n🛡️ 管理者の承認を待っています…",view=view)

        return
    
    await add_addon(interaction, file)

@tree.command(name="back-up", description="サーバーのバックアップを作成します")
async def backup_server(interaction: discord.Interaction):
    if not world_path:
        await interaction.response.send_message("❌ ワールドが設定されていません。`/setup`コマンドでワールドを設定してください", ephemeral=True)
        return
    
    backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

    with zipfile.ZipFile(backup_name, 'w') as backup_zip:
        for root, dirs, files in os.walk(world_path):
            for file in files:
                file_path = os.path.join(root, file)
                backup_zip.write(file_path, os.path.relpath(file_path, world_path))
    
    await interaction.response.send_message(f"✅ バックアップを作成しました", file=discord.File(backup_name))
    os.remove(backup_name)
    
client.run(TOKEN)
