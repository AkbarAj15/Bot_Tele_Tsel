import telebot
from dotenv import load_dotenv
import os
import mysql.connector

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
    reply_message = "Data Outlet:\n"
    for data in outlet_data:
        reply_message += f"Outlet ID: {data[8]}\nNama: {data[9]}\nStatus PJP: {data[10]}\nFisik: {data[11]}\nLast Update: {data[0]}\n cat periode: {data[1]}\n trx_omset:{data[12]}\n rev_omset:{data[13]}\n\n"
    
    bot.reply_to(message, reply_message)
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