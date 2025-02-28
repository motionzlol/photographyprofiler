import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime
from io import BytesIO
from PIL import Image
import aiohttp
import uuid


if not os.path.exists('photos'):
    os.makedirs('photos')

class UploadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        
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
        
        
        self._ensure_photo_directories()
    
    def _ensure_photo_directories(self):
        """Ensure all necessary photo directories exist"""
        
        if os.path.exists('profiles'):
            for filename in os.listdir('profiles'):
                if filename.endswith('.json'):
                    user_id = filename.split('.')[0]
                    user_photo_dir = f'photos/{user_id}'
                    if not os.path.exists(user_photo_dir):
                        os.makedirs(user_photo_dir)
    
    def _get_user_metadata_path(self, user_id):
        """Get the path to a user's photo metadata file"""
        return f'photos/{user_id}/metadata.json'
    
    def _get_user_folders(self, user_id):
        """Get a list of folders for the user"""
        user_dir = f'photos/{user_id}'
        
        
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        
        metadata_path = self._get_user_metadata_path(user_id)
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                return metadata.get('folders', [])
            except:
                return []
        
        return []

    def _create_folder(self, user_id, folder_name):
        """Create a new folder for the user"""
        
        folder_name = ''.join(c for c in folder_name if c.isalnum() or c in ' -_').strip()
        
        if not folder_name:
            return False, "Invalid folder name"
        
        
        user_folders = self._get_user_folders(user_id)
        
        
        if folder_name.lower() in [f.lower() for f in user_folders]:
            return False, "A folder with this name already exists"
        
        
        metadata_path = self._get_user_metadata_path(user_id)
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except:
                
                metadata = {'agreed_to_terms': False, 'folders': [], 'photos': {}}
        else:
            
            metadata = {'agreed_to_terms': False, 'folders': [], 'photos': {}}
        
        
        if 'folders' not in metadata:
            metadata['folders'] = []
        
        metadata['folders'].append(folder_name)
        
        
        folder_path = f'photos/{user_id}/{folder_name}'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        return True, folder_name

    async def _process_image(self, attachment):
        """Process an image: download, convert to PNG, optimize for mobile/PC"""
        try:
            
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        return None, "Failed to download image"
                    
                    image_data = await resp.read()
            
            
            image = Image.open(BytesIO(image_data))
            
            
            max_dimension = 1920
            
            
            width, height = image.size
            if width > max_dimension or height > max_dimension:
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))
                
                image = image.resize((new_width, new_height), Image.LANCZOS)
            
            
            output = BytesIO()
            image.save(output, format='PNG', optimize=True)
            output.seek(0)
            
            return output, None
        except Exception as e:
            return None, f"Error processing image: {str(e)}"

    async def _save_photo(self, user_id, folder_name, attachment, title=None, description=None):
        """Save a photo to the user's folder using Discord's CDN"""
        
        metadata_path = self._get_user_metadata_path(user_id)
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                if not metadata.get('agreed_to_terms', False):
                    return False, "You must agree to the terms before uploading photos"
            except:
                return False, "Error reading user metadata"
        else:
            return False, "You must agree to the terms before uploading photos"
        
        
        processed_image, error = await self._process_image(attachment)
        if error:
            return False, error
        
        
        filename = f"{uuid.uuid4().hex}.png"
        
        
        cdn_url = attachment.url
        
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            if 'photos' not in metadata:
                metadata['photos'] = {}
            
            if folder_name not in metadata['photos']:
                metadata['photos'][folder_name] = []
            
            
            photo_data = {
                'filename': filename,  
                'cdn_url': cdn_url,    
                'original_name': attachment.filename,
                'uploaded_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'title': title or attachment.filename,
                'description': description or '',
                'size': len(processed_image.getvalue())  
            }
            
            metadata['photos'][folder_name].append(photo_data)
            
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            
            return True, photo_data
        except Exception as e:
            return False, f"Error updating metadata: {str(e)}"

    @app_commands.command(
        name="upload",
        description="Upload a photo to your photography portfolio"
    )
    async def upload(self, interaction: discord.Interaction, image: discord.Attachment = None, title: str = None, description: str = None):
        """Upload a photo to your photography portfolio"""
        
        profile_path = f'profiles/{interaction.user.id}.json'
        if not os.path.exists(profile_path):
            embed = discord.Embed(
                title=f"{self.emoji['denied']} Profile Required",
                description="You need to create a photography profile first. Use `/profile` to set one up.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        
        if not image:
            
            await self._show_upload_options(interaction)
            return
        
        
        if not image.content_type or not image.content_type.startswith('image/'):
            embed = discord.Embed(
                title=f"{self.emoji['denied']} Invalid File",
                description="Please upload an image file (jpg, png, etc.)",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        
        await interaction.response.defer(ephemeral=True)
        
        
        user_id = str(interaction.user.id)
        metadata_path = self._get_user_metadata_path(user_id)
        
        has_agreed = False
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                has_agreed = metadata.get('agreed_to_terms', False)
            except:
                pass
        
        if not has_agreed:
            
            await self._show_terms_agreement(interaction)
            return
        
        
        folders = self._get_user_folders(user_id)
        
        if not folders:
            
            success, result = self._create_folder(user_id, "My Photos")
            if success:
                folders = ["My Photos"]
            else:
                embed = discord.Embed(
                    title=f"{self.emoji['denied']} Error",
                    description=f"Could not create a default folder: {result}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        
        
        view = FolderSelectionView(self, interaction.user, folders, image, title, description)
        
        embed = discord.Embed(
            title=f"{self.emoji['folder']} Select Folder",
            description="Please select a folder to upload your photo to:",
            color=discord.Color.blurple()
        )
        
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    async def _show_upload_options(self, interaction):
        """Show upload options and folder management"""
        user_id = str(interaction.user.id)
        
        
        folders = self._get_user_folders(user_id)
        
        embed = discord.Embed(
            title=f"{self.emoji['camera']} Photo Upload",
            description="Use this command to upload photos to your photography portfolio.",
            color=discord.Color.blurple()
        )
        
        embed.add_field(
            name="How to Upload",
            value="Use `/upload image:<your image>` to upload a photo.",
            inline=False
        )
        
        if folders:
            folders_text = "\n".join([f"{self.emoji['folder']} {folder}" for folder in folders])
            embed.add_field(
                name="Your Folders",
                value=folders_text,
                inline=False
            )
        else:
            embed.add_field(
                name="Folders",
                value="You don't have any folders yet. Create one to organize your photos.",
                inline=False
            )
        
        
        view = discord.ui.View()
        
        
        new_folder_button = discord.ui.Button(
            label="Create Folder",
            style=discord.ButtonStyle.primary,
            emoji=self.emoji['folder']
        )
        
        async def new_folder_callback(button_interaction):
            if button_interaction.user.id != interaction.user.id:
                await button_interaction.response.send_message("You can't manage someone else's folders.", ephemeral=True)
                return
            
            modal = discord.ui.Modal(title="Create New Folder")
            
            folder_name_input = discord.ui.TextInput(
                label="Folder Name",
                placeholder="Enter a name for your new folder",
                style=discord.TextStyle.short,
                max_length=50,
                required=True
            )
            
            modal.add_item(folder_name_input)
            
            async def modal_callback(modal_interaction):
                success, result = self._create_folder(str(interaction.user.id), folder_name_input.value)
                
                if success:
                    embed = discord.Embed(
                        title=f"{self.emoji['check']} Folder Created",
                        description=f"Folder \"{result}\" has been created successfully.",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title=f"{self.emoji['denied']} Error",
                        description=f"Could not create folder: {result}",
                        color=discord.Color.red()
                    )
                
                await modal_interaction.response.send_message(embed=embed, ephemeral=True)
            
            modal.on_submit = modal_callback
            await button_interaction.response.send_modal(modal)
        
        new_folder_button.callback = new_folder_callback
        view.add_item(new_folder_button)
        
        
        metadata_path = self._get_user_metadata_path(user_id)
        has_agreed = False
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                has_agreed = metadata.get('agreed_to_terms', False)
            except:
                pass
        
        
        terms_status = f"{self.emoji['check']} Agreed" if has_agreed else f"{self.emoji['denied']} Not Agreed"
        embed.add_field(
            name="Terms Agreement",
            value=f"Status: {terms_status}",
            inline=False
        )
        
        
        if not has_agreed:
            terms_button = discord.ui.Button(
                label="Agree to Terms",
                style=discord.ButtonStyle.secondary,
                emoji=self.emoji['pinned']
            )
            
            async def terms_callback(button_interaction):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message("You can't agree to terms for someone else.", ephemeral=True)
                    return
                
                await button_interaction.response.defer(ephemeral=True)
                await self._show_terms_agreement(interaction, followup=button_interaction)
            
            terms_button.callback = terms_callback
            view.add_item(terms_button)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _show_terms_agreement(self, interaction, followup=None):
        """Show terms agreement to the user"""
        embed = discord.Embed(
            title=f"{self.emoji['pinned']} Terms Agreement",
            description="Before uploading photos, you must agree to the following terms:",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📝 Terms of Use",
            value=(
                "By uploading photos, you agree that:\n\n"
                "1. You are the copyright owner of all photos you upload.\n"
                "2. You grant us a non-exclusive license to display your photos in several Discord servers.\n"
                "3. All photos will be converted to PNG format for compatibility.\n"
                "4. Photos may be resized to ensure proper display on all devices.\n"
                "5. You retain all rights to your photos and can delete them at any time.\n"
                "6. You acknowledge that whilst your photos are on our platform we have free will to use them however we like.\n"
                "7. You acknowledge that all uploaded content must comply with Discord's Terms of Service."
            ),
            inline=False
        )
        
        view = discord.ui.View()
        
        agree_button = discord.ui.Button(
            label="I Agree",
            style=discord.ButtonStyle.success,
            emoji=self.emoji['check']
        )
        
        async def agree_callback(button_interaction):
            if button_interaction.user.id != interaction.user.id:
                await button_interaction.response.send_message("You can't agree to terms for someone else.", ephemeral=True)
                return
            
            user_id = str(interaction.user.id)
            
            
            user_dir = f'photos/{user_id}'
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            
            
            metadata_path = self._get_user_metadata_path(user_id)
            
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                except:
                    metadata = {'folders': [], 'photos': {}}
            else:
                metadata = {'folders': [], 'photos': {}}
            
            metadata['agreed_to_terms'] = True
            metadata['agreed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            
            success_embed = discord.Embed(
                title=f"{self.emoji['check']} Terms Accepted",
                description="You have successfully agreed to the terms. You can now upload photos.",
                color=discord.Color.green()
            )
            
            await button_interaction.response.send_message(embed=success_embed, ephemeral=True)
        
        agree_button.callback = agree_callback
        view.add_item(agree_button)
        
        cancel_button = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            emoji=self.emoji['denied']
        )
        
        async def cancel_callback(button_interaction):
            if button_interaction.user.id != interaction.user.id:
                await button_interaction.response.send_message("You can't cancel for someone else.", ephemeral=True)
                return
            
            cancel_embed = discord.Embed(
                title=f"{self.emoji['denied']} Cancelled",
                description="You must agree to the terms before uploading photos.",
                color=discord.Color.red()
            )
            
            await button_interaction.response.send_message(embed=cancel_embed, ephemeral=True)
        
        cancel_button.callback = cancel_callback
        view.add_item(cancel_button)
        
        if followup:
            await followup.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(
        name="photos",
        description="View your or someone else's photography portfolio"
    )
    async def photos(self, interaction: discord.Interaction, user: discord.Member = None):
        """View photos in a user's portfolio"""
        target_user = user or interaction.user
        user_id = str(target_user.id)
        
        
        profile_path = f'profiles/{user_id}.json'
        if not os.path.exists(profile_path):
            if target_user == interaction.user:
                embed = discord.Embed(
                    title=f"{self.emoji['denied']} Profile Required",
                    description="You need to create a photography profile first. Use `/profile` to set one up.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title=f"{self.emoji['denied']} No Profile",
                    description=f"{target_user.display_name} doesn't have a photography profile yet.",
                    color=discord.Color.red()
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        
        metadata_path = self._get_user_metadata_path(user_id)
        
        if not os.path.exists(metadata_path):
            if target_user == interaction.user:
                embed = discord.Embed(
                    title=f"{self.emoji['camera']} No Photos",
                    description="You haven't uploaded any photos yet. Use `/upload` to add some!",
                    color=discord.Color.blue()
                )
            else:
                embed = discord.Embed(
                    title=f"{self.emoji['camera']} No Photos",
                    description=f"{target_user.display_name} hasn't uploaded any photos yet.",
                    color=discord.Color.blue()
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=target_user == interaction.user)
            return
        
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            photos_by_folder = metadata.get('photos', {})
            
            if not photos_by_folder:
                if target_user == interaction.user:
                    embed = discord.Embed(
                        title=f"{self.emoji['camera']} No Photos",
                        description="You haven't uploaded any photos yet. Use `/upload` to add some!",
                        color=discord.Color.blue()
                    )
                else:
                    embed = discord.Embed(
                        title=f"{self.emoji['camera']} No Photos",
                        description=f"{target_user.display_name} hasn't uploaded any photos yet.",
                        color=discord.Color.blue()
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=target_user == interaction.user)
                return
            
            
            await self._show_folder_selection(interaction, target_user, photos_by_folder)
        
        except Exception as e:
            embed = discord.Embed(
                title=f"{self.emoji['denied']} Error",
                description=f"An error occurred while loading photos: {str(e)}",
                color=discord.Color.red()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def _show_folder_selection(self, interaction, target_user, photos_by_folder):
        """Show folder selection for viewing photos"""
        embed = discord.Embed(
            title=f"{self.emoji['folder']} {target_user.display_name}'s Photo Gallery",
            description="Select a folder to view photos:",
            color=discord.Color.blurple()
        )
        
        
        total_photos = sum(len(photos) for photos in photos_by_folder.values())
        embed.set_footer(text=f"Total photos: {total_photos}")
        
        view = discord.ui.View()
        
        
        select = discord.ui.Select(
            placeholder="Choose a folder",
            options=[
                discord.SelectOption(
                    label=folder_name,
                    value=folder_name,
                    emoji=self.emoji['folder'],
                    description=f"{len(photos)} photos"
                )
                for folder_name, photos in photos_by_folder.items()
            ]
        )
        
        async def select_callback(select_interaction):
            folder_name = select.values[0]
            await select_interaction.response.defer()
            
            
            await self._show_photos_in_folder(interaction, target_user, photos_by_folder, folder_name)
        
        select.callback = select_callback
        view.add_item(select)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=interaction.user == target_user)
    
    async def _show_photos_in_folder(self, interaction, target_user, photos_by_folder, folder_name):
        """Show photos in the selected folder"""
        if folder_name not in photos_by_folder or not photos_by_folder[folder_name]:
            embed = discord.Embed(
                title=f"{self.emoji['folder']} {folder_name}",
                description="This folder is empty.",
                color=discord.Color.blurple()
            )
            
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        photos = photos_by_folder[folder_name]
        
        
        browser = PhotoBrowserView(self, interaction.user, target_user, folder_name, photos)
        await browser.start(interaction)

class FolderSelectionView(discord.ui.View):
    def __init__(self, cog, user, folders, image, title, description):
        super().__init__(timeout=300)
        self.cog = cog
        self.user = user
        self.folders = folders
        self.image = image
        self.title = title
        self.description = description
        
        
        self._add_folder_buttons()
    
    def _add_folder_buttons(self):
        """Add buttons for each folder"""
        for folder in self.folders:
            button = discord.ui.Button(
                label=folder,
                style=discord.ButtonStyle.secondary,
                emoji=self.cog.emoji['folder']
            )
            
            
            async def callback(interaction, folder_name=folder):
                if interaction.user.id != self.user.id:
                    await interaction.response.send_message("You can't upload to someone else's folder.", ephemeral=True)
                    return
                
                await interaction.response.defer(ephemeral=True)
                
                
                success, result = await self.cog._save_photo(
                    str(self.user.id),
                    folder_name,
                    self.image,
                    self.title,
                    self.description
                )
                
                if success:
                    embed = discord.Embed(
                        title=f"{self.cog.emoji['check']} Photo Uploaded",
                        description=f"Your photo has been successfully uploaded to \"{folder_name}\"!",
                        color=discord.Color.green()
                    )
                    
                    
                    embed.add_field(
                        name="Title",
                        value=result['title'],
                        inline=True
                    )
                    
                    if result.get('description'):
                        embed.add_field(
                            name="Description",
                            value=result['description'],
                            inline=True
                        )
                    
                    embed.add_field(
                        name="Uploaded At",
                        value=result['uploaded_at'],
                        inline=True
                    )
                    
                    
                    size_kb = result['size'] / 1024
                    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                    
                    embed.add_field(
                        name="Size",
                        value=size_str,
                        inline=True
                    )
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title=f"{self.cog.emoji['denied']} Upload Failed",
                        description=f"Could not upload photo: {result}",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
            
            
            button.callback = callback
            self.add_item(button)
        
        
        new_folder_button = discord.ui.Button(
            label="New Folder",
            style=discord.ButtonStyle.primary,
            emoji=self.cog.emoji['folder']
        )
        
        async def new_folder_callback(interaction):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("You can't create folders for someone else.", ephemeral=True)
                return
            
            modal = discord.ui.Modal(title="Create New Folder")
            
            folder_name_input = discord.ui.TextInput(
                label="Folder Name",
                placeholder="Enter a name for your new folder",
                style=discord.TextStyle.short,
                max_length=50,
                required=True
            )
            
            modal.add_item(folder_name_input)
            
            async def modal_callback(modal_interaction):
                success, result = self.cog._create_folder(str(self.user.id), folder_name_input.value)
                
                if success:
                    
                    self.folders.append(result)
                    
                    
                    self.clear_items()
                    self._add_folder_buttons()
                    
                    embed = discord.Embed(
                        title=f"{self.cog.emoji['folder']} Select Folder",
                        description=f"Folder \"{result}\" created! Please select a folder to upload your photo to:",
                        color=discord.Color.blurple()
                    )
                    
                    await modal_interaction.response.edit_message(embed=embed, view=self)
                else:
                    embed = discord.Embed(
                        title=f"{self.cog.emoji['denied']} Error",
                        description=f"Could not create folder: {result}",
                        color=discord.Color.red()
                    )
                    
                    await modal_interaction.response.send_message(embed=embed, ephemeral=True)
            
            modal.on_submit = modal_callback
            await interaction.response.send_modal(modal)
        
        new_folder_button.callback = new_folder_callback
        self.add_item(new_folder_button)

    async def on_timeout(self):
        """Handle view timeout"""
        try:
            embed = discord.Embed(
                title=f"{self.cog.emoji['denied']} Timed Out",
                description="Folder selection timed out. Please try again.",
                color=discord.Color.red()
            )
            await self.message.edit(embed=embed, view=None)
        except:
            pass

class PhotoBrowserView(discord.ui.View):
    def __init__(self, cog, user, target_user, folder_name, photos):
        super().__init__(timeout=300)
        self.cog = cog
        self.user = user
        self.target_user = target_user
        self.folder_name = folder_name
        self.photos = photos
        self.current_index = 0
        
        
        self._add_navigation_buttons()
    
    def _add_navigation_buttons(self):
        """Add navigation buttons for photo browsing"""
        
        prev_button = discord.ui.Button(
            label="Previous",
            style=discord.ButtonStyle.secondary,
            emoji=self.cog.emoji['arrowleft'],
            disabled=self.current_index == 0
        )
        
        async def prev_callback(interaction):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("You can't browse someone else's photos.", ephemeral=True)
                return
            
            self.current_index = max(0, self.current_index - 1)
            await self.update_view(interaction)
        
        prev_button.callback = prev_callback
        self.add_item(prev_button)
        
        
        next_button = discord.ui.Button(
            label="Next",
            style=discord.ButtonStyle.secondary,
            emoji=self.cog.emoji['arrowright'],
            disabled=self.current_index == len(self.photos) - 1
        )
        
        async def next_callback(interaction):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("You can't browse someone else's photos.", ephemeral=True)
                return
            
            self.current_index = min(len(self.photos) - 1, self.current_index + 1)
            await self.update_view(interaction)
        
        next_button.callback = next_callback
        self.add_item(next_button)
    
    async def start(self, interaction):
        """Start the photo browser"""
        await self.update_view(interaction)
    
    async def update_view(self, interaction):
        """Update the view with the current photo using CDN URL"""
        photo = self.photos[self.current_index]
        
        
        embed = discord.Embed(
            title=f"{self.cog.emoji['camera']} {photo['title']}",
            description=photo.get('description', ''),
            color=discord.Color.blurple()
        )
        
        
        embed.set_image(url=photo['cdn_url'])
        
        
        embed.add_field(
            name="Uploaded",
            value=photo['uploaded_at'],
            inline=True
        )
        
        
        size_kb = photo['size'] / 1024
        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
        
        embed.add_field(
            name="Size",
            value=size_str,
            inline=True
        )
        
        embed.set_footer(text=f"Photo {self.current_index + 1} of {len(self.photos)}")
        
        
        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.send_message(embed=embed, view=self, ephemeral=self.user == self.target_user)
        except Exception as e:
            embed = discord.Embed(
                title=f"{self.cog.emoji['denied']} Error",
                description=f"Could not load photo: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def on_timeout(self):
        """Handle view timeout"""
        try:
            embed = discord.Embed(
                title=f"{self.cog.emoji['denied']} Timed Out",
                description="Photo browsing timed out. Please try again.",
                color=discord.Color.red()
            )
            await self.message.edit(embed=embed, view=None)
        except:
            pass

async def setup(bot):
    await bot.add_cog(UploadCog(bot))