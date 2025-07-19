import os
import discord
from discord.ext import commands
from discord.ui import View, Select, Button
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 1268648957391671458
TRUSTED_ROLE_ID = 1368606082674724916
activated_channel_id = None
user_states = {}

GAMES = [
    ("Black Ops 6", "https://upload.wikimedia.org/wikipedia/commons/1/1b/Call_of_Duty_-_Black_Ops_6_Logo.svg"),
    ("Warzone", "https://seeklogo.com/images/C/call-of-duty-warzone-logo-373696B4F4-seeklogo.com.png"),
    ("Rocket League", "https://seeklogo.com/images/R/rocket-league-logo-481589.png"),
    ("Overwatch 2", "https://upload.wikimedia.org/wikipedia/commons/4/44/Overwatch_2_logo.png"),
    ("Marvel Rivals", "https://i.imgur.com/MarvelRivals.png"),
    ("Valorant", "https://cdn.citypng.com/valorant-white-logo.png"),
    ("Fortnite", "https://upload.wikimedia.org/wikipedia/commons/e/ec/Fortnite_Logo.svg"),
    ("CS 2", "https://upload.wikimedia.org/wikipedia/commons/3/3d/Counter-Strike_2_logo.svg"),
    ("GTA V", "https://images.vecteezy.com/graphics/original/429/gta-v-logo-transparent-png.png"),
    ("League of Legends", "https://seeklogo.com/images/L/league-of-legends-logo-492021.png"),
    ("Roblox", "https://upload.wikimedia.org/wikipedia/commons/7/73/Roblox_Logo_2025.svg")
]

def has_trusted_role(member):
    return discord.utils.get(member.roles, id=TRUSTED_ROLE_ID) is not None

class RequestView(View):
    def __init__(self, user=None):
        super().__init__(timeout=None)
        self.user = user
        self.selected_game = None
        self.selected_amount = None
        self.add_item(GameSelect(self))
        self.add_item(QuantitySelect(self))

class GameSelect(Select):
    def __init__(self, panel):
        self.panel = panel
        options = [
            discord.SelectOption(label=name, value=name, description=f"Buy {name}", emoji="🎮") for name, logo in GAMES
        ]
        super().__init__(placeholder="🎮 Choose a game", min_values=1, max_values=1, options=options)

    async def callback(self, interaction):
        if interaction.user != self.panel.user:
            await interaction.response.send_message("❌ This is not your request panel.", ephemeral=True)
            return
        self.panel.selected_game = self.values[0]
        await interaction.response.send_message(f"✅ Game selected: **{self.values[0]}**", ephemeral=True)

class QuantitySelect(Select):
    def __init__(self, panel):
        self.panel = panel
        options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(1, 21)]  # من 1 إلى 20
        super().__init__(placeholder="🔹 Select quantity", min_values=1, max_values=1, options=options)

    async def callback(self, interaction):
        if interaction.user != self.panel.user:
            await interaction.response.send_message("❌ This is not your request panel.", ephemeral=True)
            return

        if not has_trusted_role(interaction.user):
            await interaction.response.send_message("❌ Only members with the trusted role can use this.", ephemeral=True)
            return

        self.panel.selected_amount = self.values[0]
        user_states[interaction.user.id] = {
            "step": "price",
            "game": self.panel.selected_game,
            "amount": self.panel.selected_amount,
            "channel": interaction.channel
        }
        await interaction.response.send_message("💰 Please enter the price in EGP.", ephemeral=True)

class PostControl(View):
    def __init__(self, author_id, author_mention):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.author_mention = author_mention

    @discord.ui.button(label="🔍 Show requester", style=discord.ButtonStyle.secondary)
    async def show_requester(self, interaction: discord.Interaction, button: Button):
        user = await interaction.client.fetch_user(self.author_id)
        await interaction.response.send_message(f"🔎 Request was made by: {user.mention}", ephemeral=True)

    @discord.ui.button(label="📨 Contact requester", style=discord.ButtonStyle.success)
    async def contact_requester(self, interaction: discord.Interaction, button: Button):
        try:
            user = await interaction.client.fetch_user(self.author_id)
            await user.send(f"{interaction.user.mention} wants to contact you regarding your account request.")
            await interaction.response.send_message("✅ DM sent to the requester.", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Failed to send DM. The requester might have DMs disabled.", ephemeral=True)

    @discord.ui.button(label="🗑️ Delete post", style=discord.ButtonStyle.danger)
    async def delete_post(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id == self.author_id:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("❌ Only the requester can delete this post.", ephemeral=True)

    @discord.ui.button(label="🎮 Create Order", style=discord.ButtonStyle.primary)
    async def create_order_panel(self, interaction: discord.Interaction, button: Button):
        if not has_trusted_role(interaction.user):
            await interaction.response.send_message("❌ Only members with the trusted role can use this.", ephemeral=True)
            return
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🆕 New Account Request",
                description="Please use the menu below to choose a game and quantity.",
                color=discord.Color.green()
            ),
            view=RequestView(user=interaction.user),
            ephemeral=True
        )

class PanelStarter(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎮 Create Order", style=discord.ButtonStyle.primary)
    async def create_order(self, interaction: discord.Interaction, button: Button):
        if not has_trusted_role(interaction.user):
            await interaction.response.send_message("❌ Only members with the trusted role can use this.", ephemeral=True)
            return
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🆕 New Account Request",
                description="Please use the menu below to choose a game and quantity.",
                color=discord.Color.green()
            ),
            view=RequestView(user=interaction.user),
            ephemeral=True
        )

@bot.event
async def on_ready():
    print("✅ Bot is ready!")
    keep_alive()

@bot.event
async def on_message(message):
    global activated_channel_id
    if message.author == bot.user:
        return

    if message.content == "Activate the bot!" and message.author.id == OWNER_ID:
        activated_channel_id = message.channel.id
        await message.channel.send(
            embed=discord.Embed(
                title="『𝚃𝚆𝙸𝙽𝚂 𝚂𝚃𝙾𝚁𝙴 𝙰𝙲𝙲𝙾𝚄𝙽𝚃 𝙾𝚁𝙳𝙴𝚁』",
                description="Use the button below to create a new account order panel.",
                color=discord.Color.purple()
            ),
            view=PanelStarter()
        )
        return

    if message.channel.id != activated_channel_id:
        return

    if not has_trusted_role(message.author):
        await message.delete()
        return

    state = user_states.get(message.author.id)

    if state and state["step"] == "price":
        user_states[message.author.id]["price"] = message.content
        user_states[message.author.id]["step"] = "details"
        await message.delete()
        embed = discord.Embed(description="📝 Please enter the details of your request.", color=discord.Color.orange())
        await message.channel.send(embed=embed, delete_after=15)
        return

    if state and state["step"] == "details":
        game = state["game"]
        amount = state["amount"]
        price = state["price"]
        details = message.content
        await message.delete()
        view = PostControl(author_id=message.author.id, author_mention=message.author.mention)
        embed = discord.Embed(
            title="🎮 New Account Request",
            description=f"**Game:** {game}\n**Amount:** {amount} account{'s' if amount != '1' else ''}\n**Price:** {price} EGP\n**Details:** {details}",
            color=discord.Color.blurple()
        )
        await state["channel"].send("||@everyone||", embed=embed, view=view)
        del user_states[message.author.id]
        return

    if not state:
        await message.delete()

bot.run(os.getenv("TOKEN"))
