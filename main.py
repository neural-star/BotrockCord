import datetime
import zipfile
import shutil
import json
import os

import discord
from discord import app_commands
from discord.ui import Button, View

TOKEN = ""

ADMIN = None
USER_IDs = [ADMIN]
CHECK = True
BASE_PATH = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Packages\\Microsoft.MinecraftUWP_8wekyb3d8bbwe\\LocalState\\games\\com.mojang\\minecraftWorlds"
world_path = "\\None"
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

async def add_addon(interaction: discord.Interaction,file: discord.Attachment, alert: bool = True):
    await interaction.response.defer(ephemeral=True)
    path = file.filename + ".zip"
    await file.save(file.filename)
    os.rename(file.filename, path)
    
    with zipfile.ZipFile(path, "r") as zip_ref:
        zip_ref.extractall("tmp")
    os.remove(path)
    e = False
    
    for sub in os.listdir("tmp"):
        manifest_path = os.path.join("tmp", sub, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            resource_pack_path = os.path.join(world_path, "resource_packs", sub)
            behavior_pack_path = os.path.join(world_path, "behavior_packs", sub)
            if os.path.exists(resource_pack_path) and OVERWRITE:
                shutil.rmtree(resource_pack_path)
            if os.path.exists(behavior_pack_path) and OVERWRITE:
                shutil.rmtree(behavior_pack_path)
            try:
                if data["modules"][0]["type"] == "resources":
                    shutil.move(os.path.join("tmp", sub), resource_pack_path)
                elif data["modules"][0]["type"] == "data":
                    shutil.move(os.path.join("tmp", sub), behavior_pack_path)
            except shutil.Error:
                e = True
                await interaction.followup.send(f"❌ このアドオンは既に追加されています", ephemeral=True)
    if not e:
        if alert:
            await interaction.followup.send(f"✅ アドオンを追加しました", ephemeral=True)
    shutil.rmtree("tmp")

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
    await interaction.response.send_message(f"name: {os.path.basename(world_path)}\ncheck: {CHECK}\noverwrite: {OVERWRITE}\nadmin: {ADMIN}\nusers: {USER_IDs}\ntimeout: {TIMEOUT}",
                                            ephemeral=True)

@tree.command(name="addon", description="サーバーにアドオンを追加します")
async def addon(interaction: discord.Interaction, file: discord.Attachment):
    name = file.filename
    if not name.endswith((".mcaddon", ".mcpack", ".zip")):
        await interaction.response.send_message(
            "❌ 無効なファイル形式です。`.mcaddon, .mcpack, .zip`のいずれかの拡張子のファイルをアップロードしてください",
            ephemeral=True
        )
        return

    if CHECK and interaction.user.id == ADMIN:
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
