import os
import asyncio
import shlex
from telethon import TelegramClient, events, types
from telethon.errors import (
    SessionPasswordNeededError,
    FloodWaitError,
    ChatWriteForbiddenError,
    PhoneNumberInvalidError,
    AuthKeyUnregisteredError
)
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from colorama import Fore, Style, init

init(autoreset=True)

# ASCII ART
BANNER = fr"""
{Fore.CYAN} _____ _____ _____ _____      _____ 
{Fore.CYAN}|  |  |  _  |   __|_   _|    |   __|
{Fore.CYAN}|  |  |     |__   | | | _____|   __|
{Fore.CYAN}|_____|__|__|_____| |_|{Fore.RED}|_____|_____|
{Fore.GREEN}Telegram Spammer Pro v3.0 - By Xnuvers007
"""

# Konfigurasi
API_ID = 25293314
API_HASH = '8c92f1cf72128c3a27f9034748a4fe0b'
SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

# Status
class UserState:
    def __init__(self):
        self.message = "Pesan spam default 🤖"
        self.delay = 60
        self.count = 10
        self.spamming = False
        self.target_group = None
        self.all_groups = False
        self.target_groups = []
        self.stop_spam = False
        self.stats = {"sent": 0, "failed": 0}
        self.media = None
        self.sticker = None
        self.voice = None
        self.content_type = "text"  # text/media/sticker/voice

user_state = UserState()

# Fungsi Login
async def login():
    print(BANNER)
    print(f"{Fore.YELLOW}1. Login dengan akun baru")
    print(f"{Fore.YELLOW}2. Login dengan sesi yang sudah ada")
    
    while True:
        choice = input(f"{Fore.CYAN}>> Pilih opsi (1/2): ").strip()
        
        if choice == "1":
            try:
                phone = input(f"{Fore.WHITE}📱 Masukkan nomor telepon (+628xxxx): ").strip()
                session_file = os.path.join(SESSION_DIR, f"session_{phone}")
                client = TelegramClient(session_file, API_ID, API_HASH)
                
                await client.connect()
                if not await client.is_user_authorized():
                    print(f"{Fore.BLUE}⏳ Mengirim kode verifikasi...")
                    send_code = await client.send_code_request(phone)
                    
                    while True:
                        code = input(f"{Fore.WHITE}📨 Masukkan kode verifikasi: ").strip()
                        try:
                            await client.sign_in(
                                phone=phone,
                                code=code,
                                phone_code_hash=send_code.phone_code_hash
                            )
                            break
                        except SessionPasswordNeededError:
                            password = input(f"{Fore.WHITE}🔑 Masukkan password 2FA: ").strip()
                            await client.sign_in(password=password)
                
                print(f"{Fore.GREEN}✅ Login berhasil! Sesi disimpan.")
                return client
            except PhoneNumberInvalidError:
                print(f"{Fore.RED}❌ Nomor telepon tidak valid!")
            except Exception as e:
                print(f"{Fore.RED}❌ Error: {str(e)}")

        elif choice == "2":
            sessions = [f for f in os.listdir(SESSION_DIR) if f.startswith("session_")]
            if not sessions:
                print(f"{Fore.RED}❌ Tidak ada sesi yang tersedia.")
                continue

            print(f"{Fore.YELLOW}📂 Sesi yang tersedia:")
            for idx, session in enumerate(sessions, 1):
                print(f"{Fore.CYAN}{idx}. {session.replace('session_', '')}")

            while True:
                session_choice = input(f"{Fore.CYAN}>> Pilih sesi (nomor): ").strip()
                if (session_choice.isdigit() and 
                    1 <= int(session_choice) <= len(sessions)):
                    
                    session_file = os.path.join(SESSION_DIR, sessions[int(session_choice)-1])
                    client = TelegramClient(session_file, API_ID, API_HASH)
                    await client.connect()
                    
                    if await client.is_user_authorized():
                        print(f"{Fore.GREEN}✅ Login berhasil!")
                        return client
                    else:
                        print(f"{Fore.RED}⚠️ Sesi tidak valid. Silakan login ulang.")
                        break
                else:
                    print(f"{Fore.RED}❌ Pilihan tidak valid!")

        else:
            print(f"{Fore.RED}❌ Pilihan tidak valid. Silakan coba lagi.")

# Fungsi Spam
async def spam_handler(event, client):
    if user_state.spamming:
        await event.respond("⏳ Spam sedang berjalan...")
        return

    if not any([user_state.target_group, user_state.all_groups, user_state.target_groups]):
        await event.respond(f"{Fore.RED}❌ Target belum ditentukan! Gunakan `addgroup`, `addall`, atau `gcast`")
        return

    user_state.spamming = True
    user_state.stop_spam = False
    user_state.stats = {"sent": 0, "failed": 0}

    try:
        # Mendapatkan daftar grup target
        if user_state.all_groups:
            result = await client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=200,
                hash=0
            ))
            groups = [chat for chat in result.chats if isinstance(chat, types.Channel)]
        elif user_state.target_groups:
            groups = user_state.target_groups
        else:
            groups = [await client.get_entity(user_state.target_group)]

        total_groups = len(groups)
        await event.respond(f"🚀 Spam dimulai ke {total_groups} grup!")

        while user_state.spamming and (user_state.count is None or user_state.stats['sent'] < user_state.count):
            for group in groups:
                if user_state.stop_spam:
                    break
                
                try:
                    if user_state.content_type == "media" and user_state.media:
                        await client.send_file(
                            group,
                            user_state.media,
                            caption=user_state.message
                        )
                    elif user_state.content_type == "sticker" and user_state.sticker:
                        await client.send_file(
                            group,
                            user_state.sticker,
                            sticker=True
                        )
                    elif user_state.content_type == "voice" and user_state.voice:
                        await client.send_voice(
                            group,
                            user_state.voice
                        )
                    else:
                        await client.send_message(group, user_state.message)
                        
                    user_state.stats['sent'] += 1
                    print(f"{Fore.GREEN}✅ [{user_state.stats['sent']}] Pesan ke {group.title}")
                except FloodWaitError as e:
                    wait_time = e.seconds
                    print(f"{Fore.YELLOW}⏳ Flood wait! Menunggu {wait_time} detik...")
                    await asyncio.sleep(wait_time)
                except ChatWriteForbiddenError:
                    user_state.stats['failed'] += 1
                    print(f"{Fore.RED}❌ Tidak bisa menulis di {group.title}")
                except Exception as e:
                    user_state.stats['failed'] += 1
                    print(f"{Fore.RED}❌ Error: {str(e)}")
                
                await asyncio.sleep(user_state.delay)

    except Exception as e:
        print(f"{Fore.RED}❌ Error global: {str(e)}")
    finally:
        user_state.spamming = False
        await event.respond(
            f"⏹ Spam selesai!\n"
            f"📊 Statistik:\n"
            f"  • Berhasil: {user_state.stats['sent']}\n"
            f"  • Gagal: {user_state.stats['failed']}"
        )

# Handler perintah
@events.register(events.NewMessage(pattern=r'^(addgroup|addall|gcast|settings|spam|mes|help|stopspam|listgroups|setmedia|setsticker|setvoice)(.*)'))
async def handler(event):
    cmd = event.pattern_match.group(1).lower()
    args = shlex.split(event.raw_text)[1:]

    # Command HELP
    if cmd == 'help':
        help_text = f"""
{Fore.CYAN}📚 MENU BANTUAN 📚
{Fore.WHITE}addgroup [username] - Tambah grup target
{Fore.WHITE}addall - Tambah semua grup
{Fore.WHITE}gcast - Aktifkan broadcast ke semua grup
{Fore.WHITE}listgroups - Tampilkan daftar grup
{Fore.WHITE}settings - Lihat pengaturan
{Fore.WHITE}spam - Mulai spam
{Fore.WHITE}stopspam - Hentikan spam
{Fore.WHITE}mes [pesan] [delay] [jumlah] - Atur pesan
{Fore.WHITE}setmedia [file_path] - Set media untuk spam
{Fore.WHITE}setsticker [sticker_id] - Set stiker untuk spam
{Fore.WHITE}setvoice [file_path] - Set pesan suara
        """.strip()
        await event.respond(help_text)

    # Command SETMEDIA
    elif cmd == 'setmedia':
        if not args:
            await event.respond(f"{Fore.RED}❌ Format: setmedia [path/file.jpg]")
            return
            
        file_path = args[0]
        if not os.path.exists(file_path):
            await event.respond(f"{Fore.RED}❌ File tidak ditemukan!")
            return
            
        user_state.media = file_path
        user_state.content_type = "media"
        await event.respond(f"{Fore.GREEN}✅ Media diatur: {file_path}")

    # Command SETSTICKER
    elif cmd == 'setsticker':
        if not args:
            await event.respond(f"{Fore.RED}❌ Format: setsticker [sticker_id]")
            return
            
        sticker_id = args[0]
        user_state.sticker = sticker_id
        user_state.content_type = "sticker"
        await event.respond(f"{Fore.GREEN}✅ Stiker diatur: {sticker_id}")

    # Command SETVOICE
    elif cmd == 'setvoice':
        if not args:
            await event.respond(f"{Fore.RED}❌ Format: setvoice [path/audio.ogg]")
            return
            
        file_path = args[0]
        if not os.path.exists(file_path):
            await event.respond(f"{Fore.RED}❌ File tidak ditemukan!")
            return
            
        user_state.voice = file_path
        user_state.content_type = "voice"
        await event.respond(f"{Fore.GREEN}✅ Pesan suara diatur: {file_path}")

    # Command ADDGROUP
    elif cmd == 'addgroup':
        if not args:
            await event.respond(f"{Fore.RED}❌ Format: addgroup [username]")
            return
            
        username = args[0].lstrip('@')
        try:
            group = await event.client.get_entity(username)
            if not isinstance(group, types.Channel):
                await event.respond(f"{Fore.RED}❌ Bukan grup/channel valid")
                return
                
            user_state.target_group = group.id
            user_state.target_groups = []
            user_state.all_groups = False
            await event.respond(f"{Fore.GREEN}✅ Grup {group.title} ditambahkan!")
        except Exception as e:
            await event.respond(f"{Fore.RED}❌ Error: {str(e)}")

    # Command ADDALL
    elif cmd == 'addall':
        try:
            result = await event.client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=200,
                hash=0
            ))
            groups = [chat for chat in result.chats if isinstance(chat, types.Channel)]
            
            if not groups:
                await event.respond(f"{Fore.RED}❌ Tidak ada grup ditemukan")
                return
                
            user_state.target_groups = groups
            user_state.target_group = None
            user_state.all_groups = False
            await event.respond(f"{Fore.GREEN}✅ {len(groups)} grup ditambahkan!")
        except Exception as e:
            await event.respond(f"{Fore.RED}❌ Error: {str(e)}")

    # Command LISTGROUPS
    elif cmd == 'listgroups':
        try:
            result = await event.client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=200,
                hash=0
            ))
            groups = [chat for chat in result.chats if isinstance(chat, types.Channel)]
            
            if not groups:
                await event.respond(f"{Fore.RED}❌ Tidak ada grup ditemukan")
                return
                
            response = f"{Fore.CYAN}Daftar Grup ({len(groups)}):\n"
            for i, group in enumerate(groups, 1):
                response += f"{Fore.WHITE}{i}. {group.title} ({group.id})\n"
            await event.respond(response)
        except Exception as e:
            await event.respond(f"{Fore.RED}❌ Error: {str(e)}")

    # Command SPAM
    elif cmd == 'spam':
        await spam_handler(event, event.client)

    # Command STOPSPAM
    elif cmd == 'stopspam':
        user_state.stop_spam = True
        await event.respond(f"{Fore.YELLOW}⏹ Spam akan dihentikan setelah pesan terkirim")

    # Command MES
    elif cmd == 'mes':
        if len(args) < 2:
            await event.respond(f"{Fore.RED}❌ Format: mes [pesan] [delay] [jumlah]")
            return
            
        user_state.message = args[0]
        user_state.delay = int(args[1])
        user_state.count = int(args[2]) if len(args) > 2 else None
        await event.respond(f"{Fore.GREEN}✅ Pesan diupdate:\n{Fore.WHITE}{user_state.message}\nDelay: {user_state.delay}s")

    # Command SETTINGS
    elif cmd == 'settings':
        target = (
            f"Semua grup ({len(user_state.target_groups)})" if user_state.target_groups else
            "Broadcast semua grup" if user_state.all_groups else
            f"Grup ID: {user_state.target_group}" if user_state.target_group else "Belum ada"
        )
        content_type = {
            "text": "Teks",
            "media": f"Media ({user_state.media})",
            "sticker": f"Stiker ({user_state.sticker})",
            "voice": f"Suara ({user_state.voice})"
        }[user_state.content_type]
        
        await event.respond(
            f"{Fore.CYAN}⚙️ PENGATURAN\n"
            f"{Fore.WHITE}Mode: {content_type}\n"
            f"Pesan: {user_state.message}\n"
            f"Delay: {user_state.delay}s\n"
            f"Jumlah: {'∞' if user_state.count is None else user_state.count}\n"
            f"Target: {target}"
        )

# Fungsi utama
async def main():
    try:
        client = await login()
        if not client:
            return
            
        print(BANNER)
        print(f"{Fore.GREEN}🚀 Bot sedang berjalan... Gunakan /help untuk panduan")
        client.add_event_handler(handler)
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Program dihentikan manual")
    except AuthKeyUnregisteredError:
        print(f"{Fore.RED}❌ Sesi tidak valid, silakan login ulang")
    except Exception as e:
        print(f"{Fore.RED}❌ Error fatal: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())