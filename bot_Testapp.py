import telebot
from dotenv import load_dotenv
import os
import mysql.connector

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("7050190911:AAFVND4zzdHZ1Cjmi595lg8LwQ4tEjzSBSo")

bot = telebot.TeleBot("7050190911:AAFVND4zzdHZ1Cjmi595lg8LwQ4tEjzSBSo")

# Database initialization
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
cursor = db.cursor()

# Function to check if a phone number is registered
def is_registered(phone_number):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (phone_number,))
    users = cursor.fetchall()
    cursor.close()

    if users:
        response = "Data Pengguna:\n"
        for user in users:
            response += f"ID: {user[0]}, NIK: {user[1]}, Nama: {user[2]}, Alamat: {user[3]}, Nomor HP: {user[4]}\n"
    else:
        response = "Tidak ada data pengguna saat ini."
    
    return users

# Command to start or greet the bot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    first_name = message.chat.first_name
    last_name = message.chat.last_name
    bot.reply_to(message,'Hallo, {} {}'.format(first_name, last_name) + '\n' + 'Silahkan masukkan nomor HP outlet Anda')
    chat_id = message.chat.id
    phone_number = message.chat.first_name
    print(chat_id)
    print(phone_number)
    # # If the phone number is registered, fetch and display data
    # if is_registered(chat_id):
    #     print(chat_id)
    #     print(phone_number)
    # else:
    #     bot.reply_to(message, "Phone number not found. Please input your data.")
    

print('Bot start running')
# Start polling
bot.infinity_polling()

# Close database connection
db.close()