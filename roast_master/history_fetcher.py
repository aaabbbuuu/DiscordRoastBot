import asyncio
import discord
from datetime import datetime, timedelta
from typing import Optional

class HistoryFetcher:
    """
    Fetches and indexes older Discord messages for better roasting context
    """
    
    def __init__(self, bot, data_manager):
        self.bot = bot
        self.data_manager = data_manager
        self.indexing_status = {}
        
    async def index_channel_history(self, channel: discord.TextChannel, days_back: int = 30, user_filter: Optional[discord.Member] = None):
        """
        Index message history from a channel
        
        Args:
            channel: The Discord channel to index
            days_back: How many days back to fetch (default: 30)
            user_filter: If specified, only fetch messages from this user
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        message_count = 0
        user_counts = {}
        
        print(f"📚 Starting history index for #{channel.name} (last {days_back} days)...")
        
        try:
            # Fetch messages in batches (Discord API limit: 100 per request)
            async for message in channel.history(limit=None, after=cutoff_date):
                # Skip bots
                if message.author.bot:
                    continue
                
                # Skip commands
                if message.content.startswith("!"):
                    continue
                
                # Apply user filter if specified
                if user_filter and message.author.id != user_filter.id:
                    continue
                
                # Store the message
                self.data_manager.add_message(message.author.id, message.content, skip_save=True)
                
                # Track counts
                message_count += 1
                user_counts[message.author.name] = user_counts.get(message.author.name, 0) + 1
                
                # Progress indicator every 100 messages
                if message_count % 100 == 0:
                    print(f"  📊 Indexed {message_count} messages...")
            
            # Save once at the end for performance
            self.data_manager._save()
            
            print(f"✅ Indexing complete! Stored {message_count} messages from {len(user_counts)} users")
            return {
                "success": True,
                "message_count": message_count,
                "user_count": len(user_counts),
                "top_users": sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
        except discord.Forbidden:
            print(f"❌ No permission to read #{channel.name}")
            return {"success": False, "error": "No permission"}
        except Exception as e:
            print(f"❌ Error indexing #{channel.name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def index_server_history(self, guild: discord.Guild, days_back: int = 30, progress_callback=None):
        """
        Index message history from all channels in a server
        
        Args:
            guild: The Discord server to index
            days_back: How many days back to fetch
            progress_callback: Optional function to call with progress updates
        """
        results = {
            "total_messages": 0,
            "total_channels": 0,
            "successful_channels": 0,
            "failed_channels": []
        }
        
        text_channels = [ch for ch in guild.text_channels if isinstance(ch, discord.TextChannel)]
        
        print(f"🏰 Starting server-wide index for {guild.name}")
        print(f"📝 Found {len(text_channels)} text channels to process")
        
        for i, channel in enumerate(text_channels):
            if progress_callback:
                await progress_callback(f"Indexing {i+1}/{len(text_channels)}: #{channel.name}")
            
            result = await self.index_channel_history(channel, days_back)
            
            if result["success"]:
                results["total_messages"] += result["message_count"]
                results["successful_channels"] += 1
            else:
                results["failed_channels"].append(channel.name)
            
            results["total_channels"] += 1
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)
        
        print(f"✅ Server index complete!")
        print(f"   📊 {results['total_messages']} messages from {results['successful_channels']}/{results['total_channels']} channels")
        
        return results
    
    async def fetch_user_deep_history(self, guild: discord.Guild, user: discord.Member, days_back: int = 90):
        """
        Fetch a specific user's message history across all channels
        Great for finding embarrassing old messages!
        
        Args:
            guild: The Discord server
            user: The target user
            days_back: How far back to search (default: 90 days)
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        messages_found = 0
        
        print(f"🔍 Deep-diving into {user.name}'s history ({days_back} days)...")
        
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=None, after=cutoff_date):
                    if message.author.id == user.id and not message.content.startswith("!"):
                        self.data_manager.add_message(user.id, message.content, skip_save=True)
                        messages_found += 1
            except discord.Forbidden:
                continue  # Skip channels we can't read
            except Exception as e:
                print(f"⚠️ Error in #{channel.name}: {e}")
                continue
        
        # Save once at the end
        self.data_manager._save()
        
        print(f"✅ Found {messages_found} messages from {user.name}")
        return messages_found
    
    async def find_embarrassing_moments(self, user_id: int, keywords: list = None) -> list:
        """
        Search through a user's history for potentially embarrassing messages
        
        Args:
            user_id: The user to search
            keywords: Optional list of keywords to search for
        
        Returns:
            List of messages that might be embarrassing
        """
        if keywords is None:
            # Default embarrassing keywords
            keywords = [
                "cringe", "embarrassing", "oops", "my bad", "sorry", 
                "mistake", "wrong", "fail", "stupid", "idiot",
                "forgot", "confused", "help", "i don't know"
            ]
        
        user_data = self.data_manager.get_user_data(user_id)
        messages = user_data.get("messages", [])
        
        embarrassing = []
        for msg in messages:
            msg_lower = msg.lower()
            # Check if any keyword appears in the message
            if any(keyword in msg_lower for keyword in keywords):
                embarrassing.append(msg)
        
        return embarrassing[:10]  # Return top 10 most embarrassing