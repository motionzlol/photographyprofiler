




import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime


if not os.path.exists('profiles'):
    os.makedirs('profiles')


def load_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            return json.load(f)
    else:
        default_config = {
            "profile_verification_channel_id": 1344388058770047006
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        
        
        self.emoji = {
            "thumbsdown": "<:thumbsdown:1344466025131016253>",
            "thumbsup": "<:thumbsup:1344465504898781235>",
            "list": "<:list:1344454108400320674>",
            "pinned": "<:pinned:1344420504961941586>",
            "camera": "<:camera:1344376732219609129>",
            "arrowright": "<:arrowright:1344358999679700993>",
            "arrowleft": "<:arrowleft:1344358830494191787>",
            "denied": "<:denied:1344358644170363002>",
            "check": "<:check:1344358431284400169>",
            "hourglass": "<:hourglass:1344358107320684544>",
            "globe": "<:globe:1344648043953262603>",
            "bird": "<:bird:1344648083958534185>",
            "apps": "<:apps:1344648062726963282>",
            "phone": "<:phone:1344649562807209984>",
            "dot": "<:dot:1344650103386013727>",
            "folder": "<:folder:1344680932640161812>"
        }

    @app_commands.command(
        name="profile",
        description="View or set up your photography profile"
    )
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        """View your profile or someone else's, or set up a new profile"""
        if user and user != interaction.user:
            
            await self.show_user_profile(interaction, user)
        else:
            
            profile_path = f'profiles/{interaction.user.id}.json'
            if os.path.exists(profile_path):
                await self.show_user_profile(interaction, interaction.user)
            else:
                
                embed = discord.Embed(
                    title=f"{self.emoji['camera']} Photography Profile",
                    description="You don't have a photography profile yet!",
                    color=discord.Color.dark_gray()
                )
                embed.add_field(name="Get Started", value="Click the button below to set up your profile.")
                
                setup_button = discord.ui.Button(label="Setup Profile", style=discord.ButtonStyle.primary, emoji=self.emoji['camera'])
                
                async def setup_callback(button_interaction):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message("You can't set up someone else's profile.", ephemeral=True)
                        return
                    
                    await button_interaction.response.defer(ephemeral=True)
                    await self.start_profile_setup(button_interaction, interaction.user)
                
                setup_button.callback = setup_callback
                
                view = discord.ui.View()
                view.add_item(setup_button)
                
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def start_profile_setup(self, interaction, user):
        """Start the profile setup wizard"""
        profile_data = {
            "user_id": user.id,
            "username": user.name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "verified": False,
            "display_name": user.display_name,
            "photography_type": "",
            "equipment": "",
            "bio": "",
            "socials": {
                "instagram": "",
                "twitter": "",
                "flickr": "",
                "500px": "",
                "website": ""
            }
        }
        
        profile_setup = ProfileSetupView(self, user, profile_data)
        await interaction.followup.send(embed=profile_setup.get_current_page(), view=profile_setup, ephemeral=True)
    
    async def show_user_profile(self, interaction, user):
        """Show a user's profile if it exists"""
        profile_path = f'profiles/{user.id}.json'
        
        if not os.path.exists(profile_path):
            if user == interaction.user:
                
                await interaction.response.send_message("You don't have a profile yet. Use `/profile` to set one up.", ephemeral=True)
            else:
                await interaction.response.send_message(f"{user.display_name} doesn't have a photography profile yet.", ephemeral=True)
            return
        
        
        with open(profile_path, 'r') as f:
            profile = json.load(f)
        
        
        if not profile.get("verified", False) and user != interaction.user and not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(f"{user.display_name}'s profile is pending verification.", ephemeral=True)
            return
        
        
        embed = discord.Embed(
            title=f"{self.emoji['camera']} {profile.get('display_name', user.display_name)}'s Photography Profile",
            description=profile.get('bio', 'No bio provided.'),
            color=discord.Color.dark_gray()
        )
        
        
        if profile.get('photography_type'):
            embed.add_field(
                name=f"{self.emoji['list']} Photography Type",
                value=profile.get('photography_type', 'Not specified'),
                inline=False
            )
        
        
        if profile.get('equipment'):
            embed.add_field(
                name=f"{self.emoji['pinned']} Equipment",
                value=profile.get('equipment', 'Not specified'),
                inline=False
            )
        
        
        socials = profile.get('socials', {})
        social_text = ""
        
        if socials.get('instagram'):
            social_text += f"{self.emoji['apps']} Instagram: [**@{socials['instagram']}**](https://instagram.com/{socials['instagram']})\n"
        
        if socials.get('twitter'):
            social_text += f"{self.emoji['bird']} Twitter/X: [**@{socials['twitter']}**](https://twitter.com/{socials['twitter']})\n"
        
        if socials.get('flickr'):
            social_text += f"{self.emoji['dot']} Flickr: [**{socials['flickr']}**](https://flickr.com/people/{socials['flickr']})\n"
        
        if socials.get('500px'):
            social_text += f"{self.emoji['dot']} 500px: [**{socials['500px']}**](https://500px.com/{socials['500px']})\n"
        
        if socials.get('website'):
            social_text += f"{self.emoji['globe']} Website: **{socials['website']}**\n"
        
        if social_text:
            embed.add_field(name=f"{self.emoji['phone']} Social Links", value=social_text, inline=False)

        
        
        status = f"{self.emoji['check']} Verified" if profile.get('verified', False) else f"{self.emoji['hourglass']} Pending Verification"
        embed.add_field(name="Status", value=status, inline=True)
        
        
        embed.set_footer(text=f"Profile created: {profile.get('created_at', 'Unknown')}")
        
        
        view = None
        if user == interaction.user:
            view = discord.ui.View()
            edit_button = discord.ui.Button(label="Edit Profile", style=discord.ButtonStyle.secondary, emoji=self.emoji['camera'])
            
            async def edit_callback(button_interaction):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message("You can't edit someone else's profile.", ephemeral=True)
                    return
                
                await button_interaction.response.defer(ephemeral=True)
                await self.start_profile_setup(button_interaction, interaction.user)
            
            edit_button.callback = edit_callback
            view.add_item(edit_button)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=user == interaction.user)
    
    async def submit_profile_for_verification(self, user, profile_data):
        """Submit a profile for admin verification"""
        
        profile_path = f'profiles/{user.id}.json'
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f, indent=4)
        
        
        try:
            channel_id = self.config["profile_verification_channel_id"]
            channel = self.bot.get_channel(channel_id)
            
            if channel:
                embed = discord.Embed(
                    title=f"{self.emoji['hourglass']} Profile Verification Request",
                    description=f"User: {user.mention} ({user.name})\nID: {user.id}",
                    color=discord.Color.yellow()
                )
                
                embed.add_field(
                    name="Photography Type",
                    value=profile_data.get('photography_type', 'Not specified'),
                    inline=False
                )
                
                embed.add_field(
                    name="Bio",
                    value=profile_data.get('bio', 'Not provided'),
                    inline=False
                )
                
                
                socials = profile_data.get('socials', {})
                social_text = ""
                
                if socials.get('instagram'):
                    social_text += f"Instagram: @{socials['instagram']}\n"
                if socials.get('twitter'):
                    social_text += f"Twitter/X: @{socials['twitter']}\n"
                if socials.get('flickr'):
                    social_text += f"Flickr: {socials['flickr']}\n"
                if socials.get('500px'):
                    social_text += f"500px: {socials['500px']}\n"
                if socials.get('website'):
                    social_text += f"Website: {socials['website']}\n"
                
                if social_text:
                    embed.add_field(name="Social Links", value=social_text, inline=False)
                
                
                view = discord.ui.View()
                approve_button = discord.ui.Button(
                    label="Approve",
                    style=discord.ButtonStyle.success,
                    emoji=self.emoji['check'],
                    custom_id=f"approve_profile:{user.id}"
                )
                reject_button = discord.ui.Button(
                    label="Reject",
                    style=discord.ButtonStyle.danger,
                    emoji=self.emoji['denied'],
                    custom_id=f"reject_profile:{user.id}"
                )
                
                view.add_item(approve_button)
                view.add_item(reject_button)
                
                await channel.send(embed=embed, view=view)
                
                return True
            else:
                print(f"Error: Could not find verification channel with ID {channel_id}")
                return False
        except Exception as e:
            print(f"Error submitting profile for verification: {e}")
            return False

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        """Handle button interactions for profile verification"""
        if not interaction.data or not interaction.data.get('custom_id'):
            return
        
        custom_id = interaction.data.get('custom_id')
        
        
        if custom_id.startswith("approve_profile:") or custom_id.startswith("reject_profile:"):
            
            if not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message("You don't have permission to verify profiles.", ephemeral=True)
                return
            
            user_id = int(custom_id.split(":")[-1])
            profile_path = f'profiles/{user_id}.json'
            
            if not os.path.exists(profile_path):
                await interaction.response.send_message("This profile no longer exists.", ephemeral=True)
                return
            
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
            
            if custom_id.startswith("approve_profile:"):
                profile_data["verified"] = True
                with open(profile_path, 'w') as f:
                    json.dump(profile_data, f, indent=4)
                
                await interaction.response.send_message(f"Profile for <@{user_id}> has been approved!", ephemeral=True)
                
                
                try:
                    user = await self.bot.fetch_user(user_id)
                    if user:
                        embed = discord.Embed(
                            title=f"{self.emoji['check']} Profile Approved",
                            description="Your photography profile has been verified and is now visible to other users!",
                            color=discord.Color.green()
                        )
                        await user.send(embed=embed)
                except:
                    pass
                
            elif custom_id.startswith("reject_profile:"):
                await interaction.response.send_message(f"Profile for <@{user_id}> has been rejected.", ephemeral=True)
                
                
                try:
                    user = await self.bot.fetch_user(user_id)
                    if user:
                        embed = discord.Embed(
                            title=f"{self.emoji['denied']} Profile Needs Revision",
                            description="Your photography profile was not approved. Please use `/profile` to edit your profile and submit it again.",
                            color=discord.Color.red()
                        )
                        await user.send(embed=embed)
                except:
                    pass
            
            
            try:
                embed = interaction.message.embeds[0]
                status = "Approved" if custom_id.startswith("approve_profile:") else "Rejected"
                embed.title = f"{self.emoji['check'] if status == 'Approved' else self.emoji['denied']} Profile {status}"
                embed.color = discord.Color.green() if status == "Approved" else discord.Color.red()
                
                await interaction.message.edit(embed=embed, view=None)
            except:
                pass


class ProfileSetupView(discord.ui.View):
    def __init__(self, cog, user, profile_data):
        super().__init__(timeout=900)  
        self.cog = cog
        self.user = user
        self.profile_data = profile_data
        self.current_page = 0
        self.total_pages = 4
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page"""
        
        self.clear_items()
        
        
        if self.current_page > 0:
            prev_button = discord.ui.Button(label="Previous", style=discord.ButtonStyle.secondary, emoji=self.cog.emoji['arrowleft'])
            prev_button.callback = self.prev_page
            self.add_item(prev_button)
        
        if self.current_page < self.total_pages - 1:
            next_button = discord.ui.Button(label="Next", style=discord.ButtonStyle.secondary, emoji=self.cog.emoji['arrowright'])
            next_button.callback = self.next_page
            self.add_item(next_button)
        
        
        if self.current_page == self.total_pages - 1:
            submit_button = discord.ui.Button(label="Submit Profile", style=discord.ButtonStyle.success, emoji=self.cog.emoji['check'])
            submit_button.callback = self.submit_profile
            self.add_item(submit_button)
    
    def get_current_page(self):
        """Return the embed for the current page"""
        if self.current_page == 0:
            
            embed = discord.Embed(
                title=f"{self.cog.emoji['camera']} Photography Profile Setup (1/4)",
                description="Welcome to the Photography Profile setup!",
                color=discord.Color.dark_gray()
            )
            
            embed.add_field(
                name="Terms of Use",
                value="By creating a profile, you agree to our community guidelines and that your profile information may be visible to other members of the server.",
                inline=False
            )
            
            embed.add_field(
                name="Disclaimer",
                value=(
                    "**-
                    "for any unsolicited messages you might receive. Exercise caution when sharing personal information.**"
                ),
                inline=False
            )
            
            embed.add_field(
                name="Next Steps",
                value="Click 'Next' to continue setting up your profile. You'll be able to specify what kind of photography you do, your equipment, and your social media handles.",
                inline=False
            )
        
        elif self.current_page == 1:
            
            embed = discord.Embed(
                title=f"{self.cog.emoji['camera']} Photography Profile Setup (2/4)",
                description="Tell us about your photography!",
                color=discord.Color.dark_gray()
            )
            
            embed.add_field(
                name="Photography Type",
                value="What kind of photography do you do? (Landscape, Portrait, Street, Wildlife, etc.)",
                inline=False
            )
            
            photo_types_button = discord.ui.Button(label="Set Photography Types", style=discord.ButtonStyle.secondary, emoji=self.cog.emoji['list'])
            photo_types_button.callback = self.set_photography_type
            self.add_item(photo_types_button)
            
            embed.add_field(
                name="Equipment",
                value="What camera gear do you use?",
                inline=False
            )
            
            equipment_button = discord.ui.Button(label="Set Equipment", style=discord.ButtonStyle.secondary, emoji=self.cog.emoji['pinned'])
            equipment_button.callback = self.set_equipment
            self.add_item(equipment_button)
            
            
            if self.profile_data.get('photography_type'):
                embed.add_field(
                    name="Current Photography Types",
                    value=self.profile_data['photography_type'],
                    inline=False
                )
            
            if self.profile_data.get('equipment'):
                embed.add_field(
                    name="Current Equipment",
                    value=self.profile_data['equipment'],
                    inline=False
                )
        
        elif self.current_page == 2:
            
            embed = discord.Embed(
                title=f"{self.cog.emoji['camera']} Photography Profile Setup (3/4)",
                description="Connect your social media accounts!",
                color=discord.Color.dark_gray()
            )
            
            embed.add_field(
                name="Social Media Profiles",
                value=(
                    "Add your photography social media handles (username only, don't include @).\n"
                    "We'll automatically create the proper links to your profiles."
                ),
                inline=False
            )
            
            
            instagram_button = discord.ui.Button(label="Instagram", style=discord.ButtonStyle.secondary, emoji=self.cog.emoji['apps'])
            instagram_button.callback = lambda i: self.set_social_media(i, "instagram")
            self.add_item(instagram_button)
            
            
            twitter_button = discord.ui.Button(label="Twitter/X", style=discord.ButtonStyle.secondary, emoji=self.cog.emoji['bird'])
            twitter_button.callback = lambda i: self.set_social_media(i, "twitter")
            self.add_item(twitter_button)
            
            
            flickr_button = discord.ui.Button(label="Flickr", style=discord.ButtonStyle.secondary, emoji=self.cog.emoji['dot'])
            flickr_button.callback = lambda i: self.set_social_media(i, "flickr")
            self.add_item(flickr_button)
            
            
            px500_button = discord.ui.Button(label="500px", style=discord.ButtonStyle.secondary, emoji=self.cog.emoji['dot'])
            px500_button.callback = lambda i: self.set_social_media(i, "500px")
            self.add_item(px500_button)
            
            
            website_button = discord.ui.Button(label="Website", style=discord.ButtonStyle.secondary, emoji=self.cog.emoji['globe'])
            website_button.callback = lambda i: self.set_social_media(i, "website")
            self.add_item(website_button)
            
            
            socials = self.profile_data.get('socials', {})
            socials_text = ""
            
            if socials.get('instagram'):
                socials_text += f"{self.cog.emoji['apps']} Instagram: @{socials['instagram']}\n"
            if socials.get('twitter'):
                socials_text += f"{self.cog.emoji['bird']} Twitter/X: @{socials['twitter']}\n"
            if socials.get('flickr'):
                social_text += f"{self.emoji['dot']} Flickr: [**{socials['flickr']}**](https://flickr.com/people/{socials['flickr']})\n"
            if socials.get('500px'):
                social_text += f"{self.emoji['dot']} 500px: [**{socials['500px']}**](https://500px.com/{socials['500px']})\n"
            if socials.get('website'):
                socials_text += f"{self.cog.emoji['globe']} Website: {socials['website']}\n"
            
            if socials_text:
                embed.add_field(
                    name="Current Social Media",
                    value=socials_text,
                    inline=False
                )
        
        elif self.current_page == 3:
            
            embed = discord.Embed(
                title=f"{self.cog.emoji['camera']} Photography Profile Setup (4/4)",
                description="Add a bio and confirm your profile!",
                color=discord.Color.dark_gray()
            )
            
            embed.add_field(
                name="About Your Photography",
                value="Add a brief description about your photography style, interests, or anything else you'd like to share.",
                inline=False
            )
            
            bio_button = discord.ui.Button(label="Set Bio", style=discord.ButtonStyle.secondary, emoji="📝")
            bio_button.callback = self.set_bio
            self.add_item(bio_button)
            
            
            if self.profile_data.get('bio'):
                embed.add_field(
                    name="Current Bio",
                    value=self.profile_data['bio'],
                    inline=False
                )
            
            embed.add_field(
                name="Confirmation",
                value=(
                    "Once you submit your profile, it will be sent for verification by moderators "
                    "before becoming visible to other users.\n\n"
                    "Click 'Submit Profile' to complete your setup."
                ),
                inline=False
            )
        
        return embed
    
    async def prev_page(self, interaction):
        """Go to previous page"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This profile setup is not for you.", ephemeral=True)
            return
        
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_current_page(), view=self)
    
    async def next_page(self, interaction):
        """Go to next page"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This profile setup is not for you.", ephemeral=True)
            return
        
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_current_page(), view=self)
    
    async def set_photography_type(self, interaction):
        """Set photography type via modal"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This profile setup is not for you.", ephemeral=True)
            return
        
        modal = discord.ui.Modal(title="Your Photography Types")
        
        photo_type_input = discord.ui.TextInput(
            label="What kind of photography do you do?",
            placeholder="Landscape, Portrait, Street, Wildlife, etc.",
            style=discord.TextStyle.paragraph,
            max_length=200,
            required=True,
            default=self.profile_data.get('photography_type', '')
        )
        
        modal.add_item(photo_type_input)
        
        async def modal_callback(modal_interaction):
            self.profile_data['photography_type'] = photo_type_input.value
            self.update_buttons()  
            await modal_interaction.response.edit_message(embed=self.get_current_page(), view=self)
        
        modal.on_submit = modal_callback  
        await interaction.response.send_modal(modal)
    
    async def set_equipment(self, interaction):
        """Set equipment via modal"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This profile setup is not for you.", ephemeral=True)
            return
        
        modal = discord.ui.Modal(title="Your Photography Equipment")
        
        equipment_input = discord.ui.TextInput(
            label="What camera gear do you use?",
            placeholder="Camera bodies, lenses, other equipment...",
            style=discord.TextStyle.paragraph,
            max_length=300,
            required=True,
            default=self.profile_data.get('equipment', '')
        )
        
        modal.add_item(equipment_input)
        
        async def modal_callback(modal_interaction):
            self.profile_data['equipment'] = equipment_input.value
            self.update_buttons()  
            await modal_interaction.response.edit_message(embed=self.get_current_page(), view=self)
        
        modal.on_submit = modal_callback  
        await interaction.response.send_modal(modal)
    
    async def set_social_media(self, interaction, platform):
        """Set social media handle for a platform"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This profile setup is not for you.", ephemeral=True)
            return
        
        platform_labels = {
            "instagram": "Instagram Username (without @)",
            "twitter": "Twitter/X Username (without @)",
            "flickr": "Flickr Username",
            "500px": "500px Username",
            "website": "Website URL"
        }
        
        modal = discord.ui.Modal(title=f"Your {platform.title()} Profile")
        
        social_input = discord.ui.TextInput(
            label=platform_labels.get(platform, f"{platform.title()} Username"),
            placeholder="Your username only (no URLs or @)",
            style=discord.TextStyle.short,
            max_length=50,
            required=False,
            default=self.profile_data.get('socials', {}).get(platform, '')
        )
        
        modal.add_item(social_input)
        
        async def modal_callback(modal_interaction):
            if 'socials' not in self.profile_data:
                self.profile_data['socials'] = {}
            
            self.profile_data['socials'][platform] = social_input.value.strip()
            self.update_buttons()  
            await modal_interaction.response.edit_message(embed=self.get_current_page(), view=self)
        
        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)
    
    
    async def set_bio(self, interaction):
        """Set bio via modal"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This profile setup is not for you.", ephemeral=True)
            return
        
        modal = discord.ui.Modal(title="About Your Photography")
        
        bio_input = discord.ui.TextInput(
            label="Tell us about your photography",
            placeholder="Your style, interests, experience, goals...",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=True,
            default=self.profile_data.get('bio', '')
        )
        
        modal.add_item(bio_input)
        
        async def modal_callback(modal_interaction):
            self.profile_data['bio'] = bio_input.value
            self.update_buttons()
            await modal_interaction.response.edit_message(embed=self.get_current_page(), view=self)
        
        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)
    
    
    async def submit_profile(self, interaction):
        """Submit profile for verification"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This profile setup is not for you.", ephemeral=True)
            return
        
        
        self.profile_data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        
        success = await self.cog.submit_profile_for_verification(self.user, self.profile_data)
        
        if success:
            embed = discord.Embed(
                title=f"{self.cog.emoji['check']} Profile Submitted",
                description=(
                    "Your photography profile has been submitted for verification!\n\n"
                    "Once approved by moderators, your profile will be visible to other users. "
                    "You'll receive a DM notification when your profile is verified."
                ),
                color=discord.Color.green()
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            embed = discord.Embed(
                title=f"{self.cog.emoji['denied']} Error",
                description=(
                    "There was an error submitting your profile for verification. "
                    "Please try again later or contact a moderator for assistance."
                ),
                color=discord.Color.red()
            )
            
            await interaction.response.edit_message(embed=embed, view=None)

async def set_bio(self, interaction):
    """Set bio via modal"""
    if interaction.user.id != self.user.id:
        await interaction.response.send_message("This profile setup is not for you.", ephemeral=True)
        return
    
    modal = discord.ui.Modal(title="About Your Photography")
    
    bio_input = discord.ui.TextInput(
        label="Tell us about your photography",
        placeholder="Your style, interests, experience, goals...",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True,
        default=self.profile_data.get('bio', '')
    )
    
    modal.add_item(bio_input)
    
    async def modal_callback(modal_interaction):
        self.profile_data['bio'] = bio_input.value
        self.update_buttons()  
        await modal_interaction.response.edit_message(embed=self.get_current_page(), view=self)
    
    modal.on_submit = modal_callback  
    await interaction.response.send_modal(modal)
    
    async def submit_profile(self, interaction):
        """Submit profile for verification"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This profile setup is not for you.", ephemeral=True)
            return
        
        
        self.profile_data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        
        success = await self.cog.submit_profile_for_verification(self.user, self.profile_data)
        
        if success:
            embed = discord.Embed(
                title=f"{self.cog.emoji['check']} Profile Submitted",
                description=(
                    "Your photography profile has been submitted for verification!\n\n"
                    "Once approved by moderators, your profile will be visible to other users. "
                    "You'll receive a DM notification when your profile is verified."
                ),
                color=discord.Color.green()
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            embed = discord.Embed(
                title=f"{self.cog.emoji['denied']} Error",
                description=(
                    "There was an error submitting your profile for verification. "
                    "Please try again later or contact a moderator for assistance."
                ),
                color=discord.Color.red()
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
    
    async def on_timeout(self):
        """Handle timeout for the view"""
        try:
            embed = discord.Embed(
                title="Profile Setup Timed Out",
                description="The profile setup has timed out. Please use `/profile` to try again.",
                color=discord.Color.red()
            )
            
            await self.message.edit(embed=embed, view=None)
        except:
            pass


async def setup(bot):
    await bot.add_cog(ProfileCog(bot))