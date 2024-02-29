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
    cursor.execute("SELECT * FROM user_tele WHERE first_name = '{}'".format(username))
    users = cursor.fetchone()
    cursor.close()

    if users is not None:
        response ="OKE"
    else:
        response = "Tidak ada data pengguna saat ini."
    
    return users

# Command to start or greet the bot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    first_name = message.chat.first_name
    bot.reply_to(message, 'Hallo, {}'.format(first_name) + '\n' + 'Kami cek data kamu dulu ya')
    # If the phone number is registered, fetch and display data
    cursor.execute("SELECT * FROM user_tele WHERE first_name = '{}'".format(first_name))
    user_data = cursor.fetchone()
    if user_data is not None:
        # If user exists, fetch user information
        # Assuming user_data contains columns like first_name, last_name, email, etc.
        retrieved_user_id = user_data[0]
        retrieved_nik = user_data[1]
        retrieved_first_name = user_data[2]
        retrieved_alamat = user_data[3]
        retrieved_nomor_hp = user_data[4]
        # Adjust this according to your database structure
        # Reply with user information
        reply_message = f"Data Pengguna Tersedia:\nUser: {retrieved_user_id}\nNIK: {retrieved_nik}\nNama: {retrieved_first_name}\nAlamat: {retrieved_alamat}\nNomor HP: {retrieved_nomor_hp}"

        # Add more information as needed
        
        bot.reply_to(message, reply_message)
    else:
        bot.reply_to(message, "Data pengguna tidak ditemukan. Silahkan input data kamu dengan perintah /register")


# 
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
    coba.execute("INSERT INTO user_tele (id_user, NIK, first_name, alamat, nomor_hp) VALUES (%s, %s, %s, %s, %s)", (user_id, nik, first_name, address, phone_number))
    db.commit()

# Command to search data
@bot.message_handler(commands=['search'])
def search_data(message):
    bot.reply_to(message, "Silakan ikuti perintah dibawah ini untuk mencari apa yang ingin dicari:\n1. NIK\n2. Nama\n3. Alamat\n4. Nomor HP\n5. Semua data")
    
# Initialize dictionaries to store registration data and status
user_registration_data = {}
registration_status = {}

    
        
    
print('Bot start running')
# Start polling
bot.infinity_polling()

# Close database connection
db.close()