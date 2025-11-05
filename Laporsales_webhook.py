import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# 1. Konfigurasi Awal dan Variabel Global
# Token diambil dari Environment Variable, wajib diisi saat deploy
TOKEN = os.environ.get("TELEGRAM_TOKEN", '8094277197:AAF4myTiadx8kWbkWbeN2PzSmlG4AigalrPK4') 
KODE_TOKO = "FD80"
TARGET_SALES = 13372300 

# Konfigurasi Webhook (Wajib untuk layanan hosting cloud)
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://default-url-ini-harus-diganti.com") 

# Log
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Status untuk Conversation Handler
MENUNGGU_TARGET = 1
MENUNGGU_SALES = 2
MENUNGGU_STRUK = 3

# --- 2. Fungsi Bantuan ---
async def send_response(update: Update, text: str) -> None:
    """Mengirim balasan ke Topik/Thread yang sama. Mendukung Markdown."""
    if not update.effective_message:
        logger.warning("Peringatan: effective_message tidak ditemukan.")
        return

    thread_id = update.effective_message.message_thread_id
    await update.message.reply_text(text, message_thread_id=thread_id, parse_mode='Markdown')

def format_angka(n):
    """Fungsi untuk memformat angka dengan titik sebagai pemisah ribuan."""
    return f"{n:,}".replace(",", ".")

# --- 3. Fungsi Umum Bot ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menampilkan pesan sambutan."""
    await send_response(
        update,
        f"Halo! Saya Bot Sales Shift 1 untuk toko {KODE_TOKO}.\n\n"
        f"Target Sales saat ini: Rp {format_angka(TARGET_SALES)}\n\n"
        "Gunakan perintah:\n"
        "👉 `/ubah_target` untuk mengatur target baru.\n"
        "👉 `/input_sales` untuk memulai input Sales dan Struk secara bertahap."
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Membatalkan conversation."""
    context.user_data.clear()
    await send_response(update, 'Operasi dibatalkan.')
    return ConversationHandler.END

# --- 4. Fungsi Mengubah Target (/ubah_target) ---

async def ubah_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Memulai proses Conversation untuk mengubah Target Sales."""
    if update.effective_chat.type not in ['group', 'supergroup']:
        await send_response(update, "Perintah ini harus digunakan di dalam Grup Telegram.")
        return ConversationHandler.END

    await send_response(
        update,
        "Silakan masukkan **Target Sales baru** (hanya angka, cth: `8000000`):"
    )
    return MENUNGGU_TARGET

async def simpan_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menerima dan menyimpan angka target."""
    global TARGET_SALES
    try:
        input_text = update.message.text.strip().replace('.', '').replace(',', '')
        input_target = int(input_text)
        
        TARGET_SALES = input_target 
        
        await send_response(
            update,
            f"✅ **Target Sales baru** berhasil disimpan: **Rp {format_angka(input_target)}**."
        )
        await send_response(
            update,
            "Target Sales berhasil diubah. Sekarang Anda bisa mulai input data dengan /input_sales."
        )
        
        return ConversationHandler.END 

    except ValueError:
        await send_response(
            update,
            "⚠️ Format tidak valid. Pastikan Anda hanya memasukkan angka. Coba lagi:"
        )
        return MENUNGGU_TARGET

# --- 5. Fungsi Input Sales Bertahap (/input_sales) ---

async def input_sales_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Memulai proses input sales dan meminta nominal sales."""
    if update.effective_chat.type not in ['group', 'supergroup']:
        await send_response(update, "Perintah ini harus digunakan di dalam Grup Telegram.")
        return ConversationHandler.END
        
    await send_response(
        update, 
        "Silakan masukkan nominal **Sales Shift 1** (hanya angka, boleh menggunakan titik `.` sebagai pemisah ribuan):"
    )
    return MENUNGGU_SALES

async def simpan_sales(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menerima dan menyimpan Sales, lalu meminta Struk."""
    try:
        sales = int(update.message.text.strip().replace('.', '').replace(',', ''))
        
        context.user_data['sales'] = sales
        
        await send_response(update, "Sales telah diterima. Sekarang, masukkan jumlah **Struk** (hanya angka):")
        return MENUNGGU_STRUK

    except ValueError:
        await send_response(update, "⚠️ Format tidak valid. Masukkan hanya angka yang valid untuk Sales. Coba lagi:")
        return MENUNGGU_SALES

async def simpan_struk_dan_hitung(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menerima Struk, melakukan perhitungan, dan menampilkan laporan."""
    sales = context.user_data.get('sales')
    
    try:
        struk = int(update.message.text.strip().replace('.', '').replace(',', ''))
        
        if struk <= 0:
            await send_response(update, "⚠️ Struk harus lebih besar dari nol (0). Silakan coba lagi:")
            return MENUNGGU_STRUK

        # --- PERHITUNGAN ---
        avg_ticket = round(sales / struk)
        target_ach = round((sales / TARGET_SALES) * 100)
        
        # --- PEMBENTUKAN LAPORAN FINAL ---
        laporan_teks = (
            f"{KODE_TOKO}_"
            f"{format_angka(sales)}_"
            f"{struk}_"
            f"{format_angka(avg_ticket)}_"
            f"{target_ach}%"
        )
        
        context.user_data.clear()

        # --- RESPON FINAL ---
        await send_response(
            update,
            f"✅ **Perhitungan Selesai!** Data telah diproses.\n"
            "Silakan **Salin** teks laporan di bawah ini:"
        )
        
        thread_id = update.effective_message.message_thread_id
        await update.message.reply_text(
            f"```\n{laporan_teks}\n```", 
            message_thread_id=thread_id
        )
        
        return ConversationHandler.END

    except ValueError:
        await send_response(update, "⚠️ Format tidak valid. Masukkan hanya angka untuk Struk. Coba lagi:")
        return MENUNGGU_STRUK
    except Exception as e:
        logger.error(f"Error dalam simpan_struk_dan_hitung: {e}")
        context.user_data.clear()
        await send_response(update, "Terjadi kesalahan tak terduga. Silakan mulai ulang dengan /input_sales.")
        return ConversationHandler.END


# --- 6. Fungsi Utama untuk Menjalankan Bot ---
def main() -> None:
    """Menjalankan bot dalam mode Webhook untuk hosting cloud."""
    application = Application.builder().token(TOKEN).build()
    
    group_filter = filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP
    text_filter = filters.TEXT & ~filters.COMMAND

    # Handler definitions (same as before) ...
    ubah_target_handler = ConversationHandler(
        entry_points=[CommandHandler('ubah_target', ubah_target, filters=group_filter)],
        states={
            MENUNGGU_TARGET: [MessageHandler(text_filter, simpan_target)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    input_sales_handler = ConversationHandler(
        entry_points=[CommandHandler('input_sales', input_sales_start, filters=group_filter)],
        states={
            MENUNGGU_SALES: [MessageHandler(text_filter, simpan_sales)],
            MENUNGGU_STRUK: [MessageHandler(text_filter, simpan_struk_dan_hitung)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler("start", start, filters=group_filter))
    application.add_handler(ubah_target_handler)
    application.add_handler(input_sales_handler)
    application.add_handler(MessageHandler(filters.COMMAND & group_filter, lambda u, c: send_response(u, "Perintah tidak dikenal. Gunakan /start.")))
    
    
    # JALANKAN DALAM MODE WEBHOOK
    try:
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
        print(f"Bot berjalan dalam mode Webhook di port {PORT}...")
    except Exception as e:
        logger.error(f"Gagal menjalankan bot dalam mode Webhook: {e}")
        print("Coba Jalankan dalam mode Polling (Debug Lokal)")
        # Fallback ke polling hanya untuk debugging, tidak untuk 24/7
        # application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

