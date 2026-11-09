import os
import json
import aiohttp
import discord
from discord.ext import commands

# ================= SETTINGS (edit these) =================
HUB_NAME = "Rexity Hub Key Panel"
ADLINK_URL = "https://loot-link.com/s?DKeg208E"
ROLE_ID = 1568248989969547347  # your role ID
LOADSTRING = 'loadstring(game:HttpGet("https://raw.githubusercontent.com/RexityHub/x7k9m2p1/refs/heads/main/a8j3n9q2"))()'
EMBED_COLOR = 0xD81B7A
KEY_API_URL = os.getenv("KEY_API_URL", "")
DB_FILE = os.getenv("DB_FILE", "redeemed.json")
# =========================================================


def load_db():
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)


async def verify_key(key):
    """True = valid, False = invalid, None = could not check."""
    if not KEY_API_URL:
        return None
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(KEY_API_URL, params={"key": key}, headers={"User-Agent": "Mozilla/5.0"}) as r:
                text = (await r.text()).strip()
                print("VERIFY:", r.status, text[:200])
                if text.lower() in ("true", "false"):
                    return text.lower() == "true"
                return None
    except Exception:
        return None


def redeemed_text(key):
    return (
        "`-- Key Has Been Redeemed --`\n"
        f"`Key - {key}`\n"
        "`Here Is Your Script Paste The Key In The Script Box`\n"
        f"```lua\n{LOADSTRING}\n```"
    )


class RedeemModal(discord.ui.Modal, title=f"Redeem Key - {HUB_NAME}"):
    key_input = discord.ui.TextInput(
        label="Key to Redeem",
        placeholder="Enter your key...",
        required=True,
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        key = self.key_input.value.strip()
        db = load_db()
        owner = db.get(key)

        if owner and owner != interaction.user.id:
            await interaction.followup.send(
                "❌ That key was already redeemed by someone else.", ephemeral=True
            )
            return

        if not owner:
            ok = await verify_key(key)
            if ok is None:
                await interaction.followup.send(
                    "⚠️ Key checking isn't available right now. Try again later.",
                    ephemeral=True,
                )
                return
            if not ok:
                await interaction.followup.send("❌ Invalid key.", ephemeral=True)
                return
            db[key] = interaction.user.id
            save_db(db)

        await interaction.followup.send(redeemed_text(key), ephemeral=True)


class Panel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        link = discord.ui.Button(
            label="Get Key",
            emoji="🔑",
            style=discord.ButtonStyle.link,
            url=ADLINK_URL,
            row=0,
        )
        others = list(self.children)
        self.clear_items()
        self.add_item(link)
        for item in others:
            self.add_item(item)

    @discord.ui.button(label="Redeem Key", emoji="🎟️", style=discord.ButtonStyle.primary,
                       custom_id="hub:redeem", row=0)
    async def redeem(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RedeemModal())

    @discord.ui.button(label="Get Script", emoji="📜", style=discord.ButtonStyle.secondary,
                       custom_id="hub:script", row=1)
    async def script(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"```lua\n{LOADSTRING}\n```", ephemeral=True
        )

    @discord.ui.button(label="Mobile", emoji="📱", style=discord.ButtonStyle.secondary,
                       custom_id="hub:mobile", row=1)
    async def mobile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(LOADSTRING, ephemeral=True)

    @discord.ui.button(label="Get Role", emoji="🏷️", style=discord.ButtonStyle.secondary,
                       custom_id="hub:role", row=2)
    async def role(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(ROLE_ID) if interaction.guild else None
        if role is None:
            await interaction.response.send_message(
                "⚠️ The role isn't set up yet.", ephemeral=True
            )
            return
        try:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                f"✅ You now have the **{role.name}** role.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I can't give that role. Move my bot role above it.", ephemeral=True
            )


class KeyBot(commands.Bot):
    async def setup_hook(self):
        self.add_view(Panel())


intents = discord.Intents.default()
intents.message_content = True
bot = KeyBot(command_prefix="!", intents=intents, status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="Rexity Hub | !panel"))


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    embed = discord.Embed(
        title=HUB_NAME,
        description="✨ **Welcome to Rexity Hub!**\nGet access in 3 easy steps:\n\n**1️⃣ Get Key**: Tap the button and finish the quick steps to receive your key.\n**2️⃣ Redeem Key**: Paste your key to claim it. It's tied to you, so keep it private.\n**3️⃣ Get Script**: Copy the script and paste your key in the script box.\n\n📱 **Mobile**: The script as plain text, easy to copy on your phone.\n🏷️ **Get Role**: Grab your member role.\n\n⏳ Keys last 12 hours. When one runs out, just grab a new one.",
        color=EMBED_COLOR,
    )
    embed.add_field(name="⚙️ Provider", value=HUB_NAME, inline=False)
    embed.timestamp = discord.utils.utcnow()
    await ctx.send(embed=embed, view=Panel())
    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass


bot.run(os.getenv("TOKEN"))

