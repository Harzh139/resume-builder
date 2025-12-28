import os
import logging
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import json
import base64
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Load .env if present, then read configuration from environment
load_dotenv()
# Bot Configuration (read from environment)
# Set these in your environment or `.env` file before running
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class ResumeOptimizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="optimize-resume", description="Optimize your resume for ATS systems")
    @app_commands.describe(
        resume="Upload your resume file (txt, pdf, or docx)",
        email="Your email address to receive the optimized resume",
        job_description="The job description you're applying for"
    )
    async def optimize_resume(
        self,
        interaction: discord.Interaction,
        resume: discord.Attachment,
        email: str,
        job_description: str
    ):
        """Slash command to optimize resume"""
        
        # Defer the response since processing will take time
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate that required env vars are present
            if not DISCORD_TOKEN or not N8N_WEBHOOK_URL:
                await interaction.followup.send(
                    "❌ Server not configured. Missing DISCORD_TOKEN or N8N_WEBHOOK_URL.",
                    ephemeral=True
                )
                return
            # Validate file type
            allowed_extensions = ['.txt', '.pdf', '.docx']
            if not any(resume.filename.lower().endswith(ext) for ext in allowed_extensions):
                await interaction.followup.send(
                    "❌ Invalid file type. Please upload a .txt, .pdf, or .docx file.",
                    ephemeral=True
                )
                return
            
            # Validate email format
            if '@' not in email or '.' not in email.split('@')[1]:
                await interaction.followup.send(
                    "❌ Invalid email format. Please provide a valid email address.",
                    ephemeral=True
                )
                return
            
            # Validate job description length
            if len(job_description) < 100:
                await interaction.followup.send(
                    "❌ Job description is too short. Please provide at least 100 characters.",
                    ephemeral=True
                )
                return
            
            # Send processing message
            processing_embed = discord.Embed(
                title="⏳ Processing your resume...",
                description="Please wait while we optimize your resume for ATS systems.",
                color=discord.Color.blue()
            )
            processing_embed.add_field(name="📄 Status", value="Resume received\n✉️ Email confirmed\n📝 Job description analyzed", inline=False)
            processing_embed.set_footer(text="This may take 30-60 seconds")
            
            await interaction.followup.send(embed=processing_embed, ephemeral=True)
            
            # Download resume content and extract text depending on file type
            resume_data = await resume.read()
            resume_text = ""

            # If PDF, try to extract text using PyPDF2
            if resume.filename.lower().endswith('.pdf'):
                try:
                    import io
                    from PyPDF2 import PdfReader

                    reader = PdfReader(io.BytesIO(resume_data))
                    pages = []
                    for page in reader.pages:
                        try:
                            text = page.extract_text() or ""
                        except Exception:
                            text = ""
                        pages.append(text)
                    resume_text = "\n".join(pages).strip()
                except Exception as e:
                    print(f"⚠️ PDF text extraction failed, falling back to raw decode: {e}")
                    resume_text = resume_data.decode('utf-8', errors='ignore')

            # If DOCX, try to extract using python-docx
            elif resume.filename.lower().endswith('.docx'):
                try:
                    import io
                    from docx import Document

                    doc = Document(io.BytesIO(resume_data))
                    resume_text = "\n".join(p.text for p in doc.paragraphs).strip()
                except Exception as e:
                    print(f"⚠️ DOCX text extraction failed, falling back to raw decode: {e}")
                    resume_text = resume_data.decode('utf-8', errors='ignore')

            # For .txt and any other types, decode as UTF-8
            else:
                resume_text = resume_data.decode('utf-8', errors='ignore')

            print(f"📤 Sending to n8n: {N8N_WEBHOOK_URL}")
            print(f"📊 Resume length: {len(resume_text)} chars")
            print(f"📧 Email: {email}")

            # Send to n8n webhook 
            async with aiohttp.ClientSession() as session:
                payload = {
                    "resume_text": resume_text,
                    "resume_filename": resume.filename,
                    "email": email,
                    "job_description": job_description,
                    "user_id": str(interaction.user.id),
                    "username": interaction.user.name,
                    "discord_channel_id": str(interaction.channel_id)
                }
                
                async with session.post(N8N_WEBHOOK_URL, json=payload) as response:
                    
                    print(f"📥 Response status: {response.status}")
                    response_text = await response.text()
                    print(f"📥 Response body: {response_text[:500]}")
                    
                    if response.status == 200:
                        try:
                            result = json.loads(response_text)
                        except:
                            result = {}
                        
                        # Send success message with results
                        success_embed = discord.Embed(
                            title="✅ Resume Optimization Complete!",
                            description=f"Your optimized resume has been sent to **{email}**",
                            color=discord.Color.green()
                        )
                        
                        if result.get('ats_score'):
                            success_embed.add_field(
                                name="📊 ATS Score",
                                value=f"**{result['ats_score']}%**",
                                inline=False
                            )
                        
                        success_embed.add_field(
                            name="📧 Next Steps",
                            value="Check your email inbox (including spam folder) for the optimized resume PDF with detailed feedback!",
                            inline=False
                        )
                        
                        success_embed.set_footer(text="ATS Resume Optimizer")
                        
                        await interaction.followup.send(embed=success_embed, ephemeral=True)
                    else:
                        # Error response
                        error_embed = discord.Embed(
                            title="❌ Error processing resume",
                            description="Something went wrong while processing your resume.",
                            color=discord.Color.red()
                        )
                        error_embed.add_field(name="Status", value=f"{response.status}", inline=False)
                        error_embed.add_field(name="Details", value="Please try again or contact support.", inline=False)
                        
                        await interaction.followup.send(embed=error_embed, ephemeral=True)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            error_embed = discord.Embed(
                title="❌ An error occurred",
                description="There was an unexpected error processing your request.",
                color=discord.Color.red()
            )
            error_embed.add_field(name="Error", value=str(e)[:1000], inline=False)
            error_embed.add_field(name="Action", value="Please try again or contact support.", inline=False)
            
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @commands.command(name="resume-help")
    async def resume_help(self, ctx):
        """Traditional command to show help"""
        embed = discord.Embed(
            title="📝 ATS Resume Optimizer - Help",
            description="Optimize your resume to pass Applicant Tracking Systems!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="How to Use (Slash Command)",
            value=(
                "Use the slash command `/optimize-resume` with:\n"
                "• **resume**: Upload your resume file (.txt, .pdf, or .docx)\n"
                "• **email**: Your email address\n"
                "• **job_description**: The full job description (min 100 chars)\n\n"
                "Example: `/optimize-resume`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📋 Requirements",
            value=(
                "• Resume must be at least 500 characters\n"
                "• Job description must be at least 100 characters\n"
                "• Supported formats: .txt, .pdf, .docx\n"
                "• File size: Under 8MB"
            ),
            inline=False
        )
        
        embed.add_field(
            name="✨ What You'll Get",
            value=(
                "• ATS compatibility score (0-100%)\n"
                "• Optimized resume tailored to the job\n"
                "• Detailed strengths and improvement areas\n"
                "• Professional PDF sent to your email"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⏱️ Processing Time",
            value="Typically 30-60 seconds",
            inline=False
        )
        
        embed.set_footer(text="Use /optimize-resume to get started!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="test-webhook")
    @commands.has_permissions(administrator=True)
    async def test_webhook(self, ctx):
        """Test webhook connectivity (admin only)"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    N8N_WEBHOOK_URL,
                    json={"test": "ping"},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    status = response.status
                    text = await response.text()
                    
                    embed = discord.Embed(
                        title="🔧 Webhook Test Results",
                        color=discord.Color.green() if status == 200 else discord.Color.red()
                    )
                    embed.add_field(name="URL", value=N8N_WEBHOOK_URL, inline=False)
                    embed.add_field(name="Status", value=f"{status}", inline=True)
                    embed.add_field(name="Response", value=text[:1000] if text else "Empty", inline=False)
                    
                    await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Webhook test failed: {str(e)}")

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    print(f'✅ Logged in as {bot.user.name} ({bot.user.id})')
    print(f'📊 Connected to {len(bot.guilds)} server(s)')
    print(f'🔗 Webhook URL: {N8N_WEBHOOK_URL}')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="resumes | /optimize-resume"
        )
    )
    print('🤖 Bot is ready!')

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param}")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ You don't have permission to use this command.")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")
        print(f"Error: {error}")

# Add the cog to the bot
async def setup():
    await bot.add_cog(ResumeOptimizer(bot))

# Run the bot
if __name__ == "__main__":
    import asyncio
    
    # Check if token is set
    if DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN":
        print("❌ Error: Please set your DISCORD_TOKEN in the script!")
        print("Get it from: https://discord.com/developers/applications")
        exit(1)
    
    if N8N_WEBHOOK_URL == "YOUR_N8N_WEBHOOK_URL":
        print("❌ Error: Please set your N8N_WEBHOOK_URL in the script!")
        print("Example: https://your-n8n.com/webhook/discord-resume")
        exit(1)
    
    logging.info("🚀 Starting Discord Resume Optimizer Bot...")

    # Validate configuration before starting
    if not DISCORD_TOKEN:
        logging.error("DISCORD_TOKEN not set. Put it in the environment or in a .env file.")
        raise SystemExit(1)

    if not N8N_WEBHOOK_URL:
        logging.error("N8N_WEBHOOK_URL not set. Put it in the environment or in a .env file.")
        raise SystemExit(1)

    logging.info(f"🔗 Will connect to webhook: {N8N_WEBHOOK_URL}")
    
    # Setup and run
    asyncio.run(setup())
    bot.run(DISCORD_TOKEN)