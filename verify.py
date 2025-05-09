import discord
from discord.ext import commands
from discord import app_commands, Interaction, ButtonStyle
import sqlite3
import os

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix="/", intents=intents)

# SQLite configuration
DB_NAME = os.getenv("DB_NAME", "verifications.db")
DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", 5))
DB_ISOLATION_LEVEL = os.getenv("DB_ISOLATION_LEVEL", None)

# Role ID for verified users
VERIFIED_ROLE_ID = int(os.getenv("VERIFIED_ROLE_ID", 1370425286608289852))  # Replace with actual role ID

MEMBER_ROLE_ID = int(os.getenv("VERIFIED_ROLE_ID", 1370425498286690466))  # Replace with actual role ID

# Connect to SQLite database with configurations
db = sqlite3.connect(DB_NAME, timeout=DB_TIMEOUT, isolation_level=DB_ISOLATION_LEVEL)
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS verifications (
    user_id TEXT PRIMARY KEY,
    cfx_username TEXT UNIQUE
)
""")
db.commit()

class VerifyButton(discord.ui.View):
    @discord.ui.button(label="Verify", style=ButtonStyle.green, custom_id="verify_button")
    async def verify(self, interaction: Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)

        cursor.execute("SELECT * FROM verifications WHERE user_id=?", (user_id,))
        result = cursor.fetchone()

        if result:
            await interaction.response.send_message("You're already verified.", ephemeral=True)
        else:
            try:
                role = interaction.guild.get_role(MEMBER_ROLE_ID)
                if role:
                    await interaction.user.add_roles(role)
                await interaction.response.send_message("✅ You have been verified and assigned a role!", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"✅ Verified, but failed to assign role. Error: {e}", ephemeral=True)

class VerifyModal(discord.ui.Modal, title="FiveM Verification"):
    username = discord.ui.TextInput(label="Cfx.re Username", placeholder="Enter your Cfx.re forum username")

    async def on_submit(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        cfx_username = self.username.value

        cursor.execute("SELECT * FROM verifications WHERE user_id=? OR cfx_username=?", (user_id, cfx_username))
        result = cursor.fetchone()

        if result:
            await interaction.response.send_message("You're already verified or this username is taken.", ephemeral=True)
        else:
            cursor.execute("INSERT INTO verifications (user_id, cfx_username) VALUES (?, ?)", (user_id, cfx_username))
            db.commit()
            try:
                role = interaction.guild.get_role(VERIFIED_ROLE_ID)
                if role:
                    await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ Verified as {cfx_username} and role assigned!", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"✅ Verified as {cfx_username}, but failed to assign role. Error: {e}", ephemeral=True)

@client.tree.command(name="verifysetup", description="Send the verification button")
@app_commands.checks.has_permissions(manage_guild=True)
async def verifysetup(interaction: Interaction):
    await interaction.response.send_message("Click the button below to verify:", view=VerifyButton())

@verifysetup.error
async def verifysetup_error(interaction: Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

@client.tree.command(name="fivemverify", description="Verify your Cfx.re username")
async def fivemverify(interaction: Interaction):
    await interaction.response.send_modal(VerifyModal())

@client.tree.command(name="forceverify", description="Force verify a user")
@app_commands.describe(user="The user to verify", cfx_username="The Cfx.re username to assign")
async def forceverify(interaction: Interaction, user: discord.User, cfx_username: str):
    if interaction.user.guild_permissions.manage_messages:
        cursor.execute("SELECT * FROM verifications WHERE user_id=? OR cfx_username=?", (str(user.id), cfx_username))
        result = cursor.fetchone()
        if result:
            await interaction.response.send_message("❌ That user or username is already verified.", ephemeral=True)
        else:
            cursor.execute("INSERT INTO verifications (user_id, cfx_username) VALUES (?, ?)", (str(user.id), cfx_username))
            db.commit()
            await interaction.response.send_message(f"✅ Forced verification: {user.mention} as `{cfx_username}`")
    else:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

@client.event
async def on_ready():
    await client.tree.sync()
    print(f"Bot ready as {client.user}")

client.run("MTM3MDQ0NDg4Njc3MTM3MjExMg.GxmK0T.yoGwUUfJBvdpzepXajUn2Yjnrprg0xlVU7eWz8")
