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
    return users

# Command to start or greet the bot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    first_name = message.chat.first_name
    bot.reply_to(message, 'Kami cek data kamu dulu ya')
    if is_registered(first_name):
        bot.reply_to(message, "Halo, {}!".format(first_name) + "\n" + "Data kamu sudah terdaftar.")
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
    coba.execute("INSERT INTO user_tele (id_user, NIK, first_name, alamat, nomor_hp) VALUES (%s, %s, %s, %s, %s)", (user_id, nik, first_name, address, phone_number))
    db.commit()

# Command to search data
@bot.message_handler(commands=['search'])
def search_data(message):
    first_name = message.chat.first_name
    if is_registered(first_name):
        bot.reply_to(message, "Silahkan berikan perintah data apa yang ingin kamu cari.")
        bot.reply_to(message, "1./Nama\n2./barang\n3./alamat\n4./email\n5./Semua data")
    else:
        bot.reply_to(message, "Data pengguna tidak ditemukan. Silahkan input data kamu dengan perintah /register")

# Handler for search data
@bot.message_handler(func=lambda message: message.text == "/Nama")
def search_nama(message):
    user_id = message.chat.id
    search_status[user_id] = "waiting_for_nama"
    # Initialize registration data for the user
    user_search_data[user_id] = {}  # Initialize an empty dictionary
    user_search_data[user_id]["first_name"] = message.chat.first_name
    
    # Ask user for nama
    bot.reply_to(message, "Silakan masukkan nama yang ingin dicari")

@bot.message_handler(func=lambda message: search_status.get(message.from_user.id) == "waiting_for_nama")
def get_nama(message):
    user_id = message.chat.id
    nama = message.text
    user_search_data[user_id]["nama"] = nama
    search_status[user_id] = "waiting_for_nama"
    cursor = db.cursor()
    cursor.execute("SELECT * FROM data_user WHERE nama_tsel = '{}'".format(nama))
    users = cursor.fetchone()
    cursor.close()
    if users is not None:
        retrieved_user_id = users[0]
        retrieved_tanggal = users[1]
        retrieved_nama = users[2]
        retrieved_alamat = users[3]
        retrieved_email = users[4]
        retrieved_nomor_hp = users[5]
        retrieved_sisa_pulsa = users[6]
        retrieved_sisa_kuota = users[7]
        retrieved_masa_aktif = users[8]
        # Adjust this according to your database structure
        # Reply with user information
        reply_message = f"Data Pengguna Tersedia:\nUser: {retrieved_user_id}\nTanggal: {retrieved_tanggal}\nNama: {retrieved_nama}\nAlamat: {retrieved_alamat}\nEmail: {retrieved_email}\nNomor HP: {retrieved_nomor_hp}\nSisa Pulsa: {retrieved_sisa_pulsa}\nSisa Kuota: {retrieved_sisa_kuota}\nMasa Aktif: {retrieved_masa_aktif}"
        bot.reply_to(message, reply_message)
        
    else:
        bot.reply_to(message, "Data pengguna tidak ditemukan.")

@bot.message_handler(func=lambda message: message.text == "/barang")
def search_barang(message):
    user_id = message.chat.id
    search_status[user_id] = "waiting_for_barang"
    # Initialize registration data for the user
    user_search_data[user_id] = {}  # Initialize an empty dictionary
    user_search_data[user_id]["first_name"] = message.chat.first_name
    
    # Ask user for barang
    bot.reply_to(message, "Silakan masukkan kode barang yang ingin dicari")
    
@bot.message_handler(func=lambda message: search_status.get(message.from_user.id) == "waiting_for_barang")
def get_barang(message):
    user_id = message.chat.id
    barang = message.text
    user_search_data[user_id]["barang"] = barang
    search_status[user_id] = "waiting_for_barang"
    cursor = db.cursor()
    cursor.execute("SELECT * FROM data_barang WHERE id_barang = '{}'".format(barang))
    users = cursor.fetchone()
    cursor.close()
    if users is not None:
        retrieved_kode_barang = users[0]
        retrieved_nama_barang = users[1]
        retrieved_harga_barang = users[2]
        retrieved_stok_barang = users[3]
        # Adjust this according to your database structure
        # Reply with user information
        reply_message = f"Data Barang Tersedia:\nKode Barang: {retrieved_kode_barang}\nNama Barang: {retrieved_nama_barang}\nHarga Barang: {retrieved_harga_barang}\nStok Barang: {retrieved_stok_barang}"
        bot.reply_to(message, reply_message)
        
    else:
        bot.reply_to(message, "Data barang tidak ditemukan.")
    
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