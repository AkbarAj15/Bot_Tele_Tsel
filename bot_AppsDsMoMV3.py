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
    host="localhost",
    user="root",
    password="",
    database="cobaBot"
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
        bot.reply_to(message, "Halo, {}!".format(first_name) + "\n" + "Silahkan Klik menu dibawah ini untuk melihat\n 1. /performance (DS)\n 2. /search (OUTLET_ID)\n")
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
    locale.setlocale(locale.LC_ALL, '')  # Mengatur lokalisasi sesuai dengan pengaturan default sistem
    for data in outlet_data:
        reply_message = f'Outlet ID: {data[0]}\nNama: {data[1]}\nStatus PJP: {data[2]}\nFisik: {data[3]}\nLast Update: {data[4]}'
    # Show the Omset Data Outlet
    omset = get_omset(outlet_id)
    for data_omset in omset:
        locale.setlocale(locale.LC_ALL, '')
        trx = data_omset[0]
        rev = data_omset[2]
        Mom_trx = data_omset[1]
        Mom_rev = data_omset[3]
        formatted_rev = locale.format_string("%.3f", rev, grouping=True).rstrip('0').rstrip(',')
        reply_message += f'\n\nOmset\nTrx: {trx}\nMoM Trx: {Mom_trx : .2f}%\nRev: {formatted_rev}\nMoM Rev: {Mom_rev : .2f}%'
    # Show the Renewal Data Outlet
    renewal = get_renewal(outlet_id)
    for data_renewal in renewal:
        trx_renewal = data_renewal[0]
        rev_renewal = data_renewal[2]
        Mom_trx_renewal = data_renewal[1]
        Mom_rev_renewal = data_renewal[3]
        formatted_rev_renewal = locale.format_string("%.3f", rev_renewal, grouping=True).rstrip('0').rstrip(',')
        reply_message += f'\n\nRenewal\nTrx: {trx_renewal}\nMoM Trx: {Mom_trx_renewal : .2f}%\nRev: {formatted_rev_renewal}\nMoM Rev: {Mom_rev_renewal: .2f}%'
    
    # Show the CVM Data Outlet
    cvm = get_cvm(outlet_id)
    for data_cvm in cvm:
        trx_cvm = data_cvm[0]
        rev_cvm = data_cvm[2]
        Mom_trx_cvm = data_cvm[1]
        Mom_rev_cvm = data_cvm[3]
        formatted_rev_cvm = locale.format_string("%.3f", rev_cvm, grouping=True).rstrip('0').rstrip(',')
        reply_message += f'\n\nCVM\nTrx: {trx_cvm}\nMoM Trx: {Mom_trx_cvm : .2f}%\nRev: {formatted_rev_cvm}\nMoM Rev: {Mom_rev_cvm : .2f}%'
    
    # Show the Omni Data Outlet
    omni = get_omni(outlet_id)
    for data_omni in omni:
        trx_omni = data_omni[0]
        rev_omni = data_omni[2]
        Mom_trx_omni = data_omni[1]
        Mom_rev_omni = data_omni[3]
        formatted_rev_omni = locale.format_string("%.3f", rev_omni, grouping=True).rstrip('0').rstrip(',')
        reply_message += f'\n\nOmni\nTrx: {trx_omni}\nMoM Trx: {Mom_trx_omni : .2f}%\nRev: {formatted_rev_omni}\nMoM Rev: {Mom_rev_omni : .2f}%'
    
    # Show the Games Data Outlet
    games = get_games(outlet_id)
    for data_games in games:
        trx_games = data_games[0]
        rev_games = data_games[2]
        Mom_trx_games = data_games[1]
        Mom_rev_games = data_games[3]
        formatted_rev_games = locale.format_string("%.3f", rev_games, grouping=True).rstrip('0').rstrip(',')
        reply_message += f'\n\nGames\nTrx: {trx_games}\nMoM Trx: {Mom_trx_games : .2f}%\nRev: {formatted_rev_games}\nMoM Rev: {Mom_rev_games : .2f}%'
        
    # Show the Voice Data Outlet
    voice = get_voice(outlet_id)
    for data_voice in voice:
        trx_voice = data_voice[0]
        rev_voice = data_voice[2]
        Mom_trx_voice = data_voice[1]
        Mom_rev_voice = data_voice[3]
        formatted_rev_voice = locale.format_string("%.3f", rev_voice, grouping=True).rstrip('0').rstrip(',')
        reply_message += f'\n\nVoice\nTrx: {trx_voice}\nMoM Trx: {Mom_trx_voice : .2f}%\nRev: {formatted_rev_voice}\nMoM Rev: {Mom_rev_voice : .2f}%'
    
    # Show the NSB Data Outlet
    nsb = get_nsb(outlet_id)
    for data_nsb in nsb:
        trx_nsb = data_nsb[0]
        rev_nsb = data_nsb[2]
        Mom_trx_nsb = data_nsb[1]
        Mom_rev_nsb = data_nsb[3]
        formatted_rev_nsb = locale.format_string("%.3f", rev_nsb, grouping=True).rstrip('0').rstrip(',')
        reply_message += f'\n\nNSB\nTrx: {trx_nsb}\nMoM Trx: {Mom_trx_nsb : .2f}%\nRev: {formatted_rev_nsb}\nMoM Rev: {Mom_rev_nsb : .2f}%'
        
    # Show the Combo Data Outlet
    combo = get_combo(outlet_id)
    for data_combo in combo:
        trx_combo = data_combo[0]
        rev_combo = data_combo[2]
        Mom_trx_combo = data_combo[1]
        Mom_rev_combo = data_combo[3]
        formatted_rev_combo = locale.format_string("%.3f", rev_combo, grouping=True).rstrip('0').rstrip(',')
        reply_message += f'\n\nCombo\nTrx: {trx_combo}\nMoM Trx: {Mom_trx_combo : .2f}%\nRev: {formatted_rev_combo}\nMoM Rev: {Mom_rev_combo : .2f}%'
    
    # Show the Internet Sakti Data Outlet
    isak = get_isak(outlet_id)
    for data_isak in isak:
        trx_isak = data_isak[0]
        rev_isak = data_isak[2]
        Mom_trx_isak = data_isak[1]
        Mom_rev_isak = data_isak[3]
        formatted_rev_isak = locale.format_string("%.3f", rev_isak, grouping=True).rstrip('0').rstrip(',')
        reply_message += f'\n\nInternet Sakti\nTrx: {trx_isak}\nMoM Trx: {Mom_trx_isak : .2f}%\nRev: {formatted_rev_isak}\nMoM Rev: {Mom_rev_isak : .2f}%'
    
    
    bot.reply_to(message, reply_message)
    
    

# Function to get data from database
def get_outlet_data(outlet_id):
    cursor = db.cursor()
    cursor.execute("SELECT outlet_id, nama, status_pjp, fisik, last_update FROM data_penjualan_ds WHERE outlet_id = %s", (outlet_id,))
    outlet_data = cursor.fetchall()
    return outlet_data

# Function Query get Omset From Database
def get_omset(outlet_id):
    cursor = db.cursor()
    cursor.execute("""SELECT trx_omset, 
                   (SUM(CASE WHEN cat_periode = 'BULAN_M' THEN trx_omset ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_omset ELSE 0 END)-1)*100 AS MoM_Trx_Omset, 
                   rev_omset, 
                   (SUM(CASE WHEN cat_periode = 'BULAN_M' THEN rev_omset ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_omset ELSE 0 END)-1)*100 AS MoM_Rev_Omset 
                   FROM data_penjualan_ds WHERE outlet_id = %s""", (outlet_id,))
    omset = cursor.fetchall()
    return omset

# Function Query get Renewal From Database
def get_renewal(outlet_id):
    cursor = db.cursor()
    cursor.execute("""SELECT trx_renewal, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_renewal ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN trx_renewal ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_renewal ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_trx_renewal,
                   rev_renewal, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_renewal ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN rev_renewal ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_renewal ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_Rev_Renewal FROM data_penjualan_ds WHERE outlet_id = %s""", (outlet_id,))
    renewal = cursor.fetchall()
    return renewal

# Function Query get CVM From Database
def get_cvm(outlet_id):
    cursor = db.cursor()
    cursor.execute("""SELECT trx_cvm, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_cvm ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN trx_cvm ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_cvm ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_trx_cvm,
                   rev_cvm, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_cvm ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN rev_cvm ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_cvm ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_Rev_cvm FROM data_penjualan_ds WHERE outlet_id = %s""", (outlet_id,))
    cvm = cursor.fetchall()
    return cvm

# Function Query get Omni From Database 
def get_omni(outlet_id):
    cursor = db.cursor()
    cursor.execute("""SELECT trx_omni, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_omni ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN trx_omni ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_omni ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_trx_omni,
                   rev_omni, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_omni ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN rev_omni ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_omni ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_Rev_omni FROM data_penjualan_ds WHERE outlet_id = %s""", (outlet_id,))
    omni = cursor.fetchall()
    return omni

# Function Query get Games From Database
def get_games(outlet_id):
    cursor = db.cursor()
    cursor.execute("""SELECT trx_games, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_games ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN trx_games ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_games ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_trx_games,
                   rev_games, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_games ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN rev_games ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_games ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_Rev_games FROM data_penjualan_ds WHERE outlet_id = %s""", (outlet_id,))
    games = cursor.fetchall()
    return games

# Function Query get Voice From Database
def get_voice(outlet_id):
    cursor = db.cursor()
    cursor.execute("""SELECT trx_voice, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_voice ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN trx_voice ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_voice ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_trx_voice,
                   rev_voice, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_voice ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN rev_voice ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_voice ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_Rev_voice FROM data_penjualan_ds WHERE outlet_id = %s""", (outlet_id,))
    voice = cursor.fetchall()
    return voice

# Function Query get NSB From Database
def get_nsb(outlet_id):
    cursor = db.cursor()
    cursor.execute("""SELECT trx_nsb, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_nsb ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN trx_nsb ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_nsb ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_trx_nsb,
                   rev_nsb, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_nsb ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN rev_nsb ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_nsb ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_Rev_nsb FROM data_penjualan_ds WHERE outlet_id = %s""", (outlet_id,))
    nsb = cursor.fetchall()
    return nsb

# Function Query get Combo From Database
def get_combo(outlet_id):
    cursor = db.cursor()
    cursor.execute("""SELECT trx_combo, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_combo ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN trx_combo ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_combo ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_trx_combo,
                   rev_combo, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_combo ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN rev_combo ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_combo ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_Rev_combo FROM data_penjualan_ds WHERE outlet_id = %s""", (outlet_id,))
    combo = cursor.fetchall()
    return combo

# Function Query get Internet Sakti From Database
def get_isak(outlet_id):
    cursor = db.cursor()
    cursor.execute("""SELECT trx_isak, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_isak ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN trx_isak ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN trx_isak ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_trx_isak,
                   rev_isak, 
                   (CASE WHEN SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_isak ELSE 0 END) <> 0 
                        THEN ((SUM(CASE WHEN cat_periode = 'BULAN_M' THEN rev_isak ELSE 0 END) / SUM(CASE WHEN cat_periode = 'BULAN_M1' THEN rev_isak ELSE 0 END) - 1) * 100) 
                        ELSE 0 END) AS MoM_Rev_isak FROM data_penjualan_ds WHERE outlet_id = %s""", (outlet_id,))
    isak = cursor.fetchall()
    return isak








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