import telebot
from dotenv import load_dotenv
import os
import mysql.connector
import locale

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

# Database initialization
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
cursor = db.cursor()
#fucntion to check if a username is registered
def is_registered(username):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user_tele WHERE username = '{}'".format(username))
    users = cursor.fetchone()
    cursor.close()
    return users

# Command to start or greet the bot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    first_name = message.chat.first_name
    bot.reply_to(message, 'Kami cek data kamu dulu ya')
    if is_registered(first_name):
        bot.reply_to(message, "Halo, {}!".format(first_name) + "\n" + "Ada yang bisa kami bantu? /search untuk mencari data.")
    else:
        bot.reply_to(message, "Data pengguna tidak ditemukan. Silahkan input data kamu dengan perintah /register")
# Command to initiate registration
@bot.message_handler(commands=['register'])
def start_registration(message):
    # Set the initial registration status for the user
    user_id = message.chat.id
    registration_status[user_id] = "waiting_for_nik"
    # Initialize registration data for the user
    user_registration_data[user_id] = {}  # Initialize an empty dictionary
    user_registration_data[user_id]["first_name"] = message.chat.first_name
    
    # Ask user for NIK
    bot.reply_to(message, "Silakan masukkan NIK Anda.")

# Handler for NIK input
@bot.message_handler(func=lambda message: registration_status.get(message.from_user.id) == "waiting_for_nik")
def get_nik(message):
    user_id = message.chat.id
    nik = message.text
    
    # Save NIK to database or session
    user_registration_data[user_id]["nik"] = nik
    
    # Update registration status
    registration_status[user_id] = "waiting_for_address"
    
    # Ask user for address
    bot.reply_to(message, "Terima kasih. Sekarang masukkan alamat Anda.")

# Handler for address input
@bot.message_handler(func=lambda message: registration_status.get(message.from_user.id) == "waiting_for_address")
def get_address(message):
    user_id = message.chat.id
    address = message.text
    
    # Save address to database or session
    user_registration_data[user_id]["address"] = address
    
    # Update registration status
    registration_status[user_id] = "waiting_for_phone_number"
    
    # Ask user for phone number
    bot.reply_to(message, "Alamat telah tersimpan. Sekarang masukkan nomor HP Anda.")

# Handler for phone number input
@bot.message_handler(func=lambda message: registration_status.get(message.from_user.id) == "waiting_for_phone_number")
def get_phone_number(message):
    user_id = message.chat.id
    phone_number = message.text
    
    # Save phone number to database or session
    user_registration_data[user_id]["phone_number"] = phone_number
    
    # Clear registration status
    del registration_status[user_id]
    
    # Save all registration data to database
    save_registration_data(user_id)
    
    # Inform user about successful registration
    bot.reply_to(message, "Registrasi berhasil. Data Anda telah terdaftar.")

def save_registration_data(user_id):
    # Retrieve user's registration data
    first_name = user_registration_data[user_id]["first_name"]
    nik = user_registration_data[user_id]["nik"]
    address = user_registration_data[user_id]["address"]
    phone_number = user_registration_data[user_id]["phone_number"]
    
    # Save data to database
    coba = db.cursor()
    coba.execute("INSERT INTO user_tele (id_user, NIK, username, alamat, nomor_hp) VALUES (%s, %s, %s, %s, %s)", (user_id, nik, first_name, address, phone_number))
    db.commit()

# Command to search data
@bot.message_handler(commands=['search'])
def search_data(message):
    first_name = message.chat.first_name
    user_id = message.chat.id
    if is_registered(first_name):
        search_status[user_id] = "waiting_for_outlet_id"
        user_search_data[user_id]= {}
        user_search_data[user_id]["first_name"] = first_name
        bot.reply_to(message, "Silahkan berikan outlet id yang ingin dicari.")
    else:
        bot.reply_to(message, "Data pengguna tidak ditemukan. Silahkan input data kamu dengan perintah /register")
@bot.message_handler(func=lambda message: search_status.get(message.from_user.id) == "waiting_for_outlet_id")
def get_penjualan(message):
    user_id = message.chat.id
    outlet_id = message.text
    user_search_data[user_id]["outlet_id"] = outlet_id
    search_status[user_id] = "waiting_for_outlet_id"
    outlet_data = get_outlet_data(outlet_id)
    if len(outlet_data) >= 2:  # Pastikan ada setidaknya dua data untuk perbandingan MoM
        for data in outlet_data:
            if data[1] == 'BULAN_M':
                current_month_trx_omset = data[12]
                current_month_rev_omset = data[13]
                current_month_trx_renewal = data[14]
                current_month_rev_renewal = data[15]
                current_month_trx_cvm = data[16]
                current_month_rev_cvm = data[17]
                current_month_trx_omni = data[18]
                current_month_rev_omni = data[19]
                current_month_trx_games = data[20]
                current_month_rev_games = data[21]
            elif data[1] == 'BULAN_M1':
                previous_month_trx_omset = data[12]
                previous_month_rev_omset = data[13]
                previous_month_trx_renewal = data[14]
                previous_month_rev_renewal = data[15]
                previous_month_trx_cvm = data[16]
                previous_month_rev_cvm = data[17]
                previous_month_trx_omni = data[18]
                previous_month_rev_omni = data[19]
                previous_month_trx_games = data[20]
                previous_month_rev_games = data[21]
        if current_month_trx_omset and current_month_rev_omset:  # Pastikan data untuk kedua bulan tersedia
           # Calculate MoM growth
            mom_trx_omset = ((current_month_trx_omset / previous_month_trx_omset) - 1)* 100
            mom_rev_omset = ((current_month_rev_omset / previous_month_rev_omset) - 1)* 100
            # mom_trx_renewal = ((current_month_trx_renewal / previous_month_trx_renewal) - 1)* 100
            # mom_rev_renewal = ((current_month_rev_renewal / previous_month_rev_renewal) - 1)* 100
            mom_trx_cvm = ((current_month_trx_cvm / previous_month_trx_cvm) - 1)* 100
            mom_rev_cvm = ((current_month_rev_cvm / previous_month_rev_cvm) - 1)* 100
            # mom_trx_omni = ((current_month_trx_omni / previous_month_trx_omni) - 1)* 100
            # mom_rev_omni = ((current_month_rev_omni / previous_month_rev_omni) - 1)* 100
            # mom_trx_games = ((current_month_trx_games / previous_month_trx_games) - 1)* 100
            # mom_rev_games = ((current_month_rev_games / previous_month_rev_games) - 1)* 100
            locale.setlocale(locale.LC_ALL, '')  # Mengatur lokalisasi sesuai dengan pengaturan default sistem
            
            # Show the Outlet id
            reply_message = f"Outlet ID: {data[8]}\nNama: {data[9]}\nStatus PJP: {data[10]}\nFisik: {data[11]}\nLast Update: {data[0]}\n\n"
            # Show the Omset MoM
            formatted_rev_omset = locale.format_string("%.3f", current_month_rev_omset, grouping=True).rstrip('0').rstrip('.')
            reply_message += f"""Omset\ntrx_omset: {current_month_trx_omset}\nMoM trx_omset: {mom_trx_omset: .2f}%\nrev_omset: {formatted_rev_omset}\nMoM rev_omset: {mom_rev_omset: .2f}%\n\n"""  # Format pesan balasan
            # # Show the Renewal MoM
            # formatted_rev_renewal = locale.format_string("%.3f", current_month_rev_renewal, grouping=True).rstrip('0').rstrip('.')
            # reply_message += f"""Renewal\ntrx_renewal: {current_month_trx_renewal}\nMoM trx_renewal: {mom_trx_renewal: .2f}%\nrev_renewal: {formatted_rev_renewal}\nMoM rev_renewal: {mom_rev_renewal: .2f}%\n"""  # Format pesan balasan
            # Show the CVM MoM
            formatted_rev_cvm = locale.format_string("%.3f", current_month_rev_cvm, grouping=True).rstrip('0').rstrip('.')
            reply_message += f"""CVM\ntrx_cvm: {current_month_trx_cvm}\nMoM trx_cvm: {mom_trx_cvm: .2f}%\nrev_cvm: {formatted_rev_cvm}\nMoM rev_cvm: {mom_rev_cvm: .2f}%\n"""  # Format pesan balasan
            # # Show the Omni MoM
            # formatted_rev_omni = locale.format_string("%.3f", current_month_rev_omni, grouping=True).rstrip('0').rstrip('.')
            # reply_message += f"""Omni\ntrx_omni: {current_month_trx_omni}\nMoM trx_omni: {mom_trx_omni: .2f}%\nrev_omni: {formatted_rev_omni}\nMoM rev_omni: {mom_rev_omni: .2f}%\n"""  # Format pesan balasan
            # Show the Games MoM
            # formatted_rev_games = locale.format_string("%.3f", current_month_rev_games, grouping=True).rstrip('0').rstrip('.')
            # reply_message += f"""Games\ntrx_games: {current_month_trx_games}\nMoM trx_games: {mom_trx_games: .2f}%\nrev_games: {formatted_rev_games}\nMoM rev_games: {mom_rev_games: .2f}%\n"""  # Format pesan balasan
            bot.reply_to(message, reply_message)
        else:
            bot.reply_to(message, "Data untuk kedua bulan tidak lengkap.")
    else:
        bot.reply_to(message, "Data untuk perbandingan MoM tidak cukup.")
# Function to get data from database
def get_outlet_data(outlet_id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM data_penjualan_ds WHERE outlet_id = %s", (outlet_id,))
    outlet_data = cursor.fetchall()
    return outlet_data

# Initialize dictionaries to store registration data and status
user_search_data = {}
user_registration_data = {}
search_status = {}
registration_status = {}
print('Bot start running')
# Start polling
bot.infinity_polling()

# Close database connection
db.close()