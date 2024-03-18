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
    users = cursor.fetchall()
    cursor.close()
    return users

# Command to start or greet the bot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    first_name = message.chat.first_name
    bot.reply_to(message, 'Kami cek data kamu dulu ya')
    if is_registered(first_name):
        bot.reply_to(message, "Halo, {}!".format(first_name) + "\n" + "Silahkan klik menu dibawah ini untuk mengecek performansi DS\n1. /search (ID DIGIPOS)\n")
    else:
        bot.reply_to(message, "Data pengguna tidak ditemukan.\nSilahkan daftarkan dirimu dengan klik perintah dibawah ini.\n/register")
# Command to initiate registration
@bot.message_handler(commands=['register'])
def start_registration(message):
    # Set the initial registration status for the user
    user_id = message.chat.id
    registration_status[user_id] = "waiting_for_id_digipos"
    # Initialize registration data for the user
    user_registration_data[user_id] = {}  # Initialize an empty dictionary
    user_registration_data[user_id]["first_name"] = message.chat.first_name
    
    # Ask user for ID DIGIPOS
    bot.reply_to(message, "Silakan masukkan ID Digipos Anda\nContoh : (4100000026)")

# Handler for NIK input
@bot.message_handler(func=lambda message: registration_status.get(message.from_user.id) == "waiting_for_id_digipos")
def get_id_digipos(message):
    user_id = message.chat.id
    id_digipos = message.text
    
    # Save id_digipos to database or session
    user_registration_data[user_id]["id_digipos"] = id_digipos
    
    # Update registration status
    registration_status[user_id] = "waiting_for_phone_number"
    
    # Ask user for address
    bot.reply_to(message, "ID Digipos Tersimpan\nSelanjutnya Masukkan Nomor Hp Anda\nContoh : (082117779034)")
 
    
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
    bot.reply_to(message, "Registrasi berhasil\nSilahkan klik menu dibawah ini untuk mengecek performansi DS\n1. /search (ID DIGIPOS)\n")

def save_registration_data(user_id):
    # Retrieve user's registration data
    first_name = user_registration_data[user_id]["first_name"]
    id_digipos = user_registration_data[user_id]["id_digipos"]
    phone_number = user_registration_data[user_id]["phone_number"]
    
    # Save data to database
    coba = db.cursor()
    coba.execute("INSERT INTO user_tele (id_user, username, id_digipos, nomor_hp) VALUES (%s, %s, %s, %s)", (user_id, first_name, id_digipos, phone_number))
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
        bot.reply_to(message, "Silahkan berikan ID Digipos yang ingin dicek performansinya\nContoh : (4100000026)")
    else:
        bot.reply_to(message, "Data pengguna tidak ditemukan.\nSilahkan daftarkan dirimu dengan klik perintah dibawah ini.\n/register")
        

@bot.message_handler(func=lambda message: search_status.get(message.from_user.id) == "waiting_for_outlet_id")
def get_penjualan(message):
    user_id = message.chat.id
    outlet_id = message.text
    user_search_data[user_id]["outlet_id"] = outlet_id
    search_status[user_id] = "waiting_for_outlet_id"
    outlet_data = get_outlet_data(outlet_id)
    if outlet_data:
        locale.setlocale(locale.LC_ALL, '')  # Mengatur lokalisasi sesuai dengan pengaturan default sistem
        for data in outlet_data:
            reply_message = f'*Semangat Pagi !!!*\n'
            reply_message += f'Berikut performance update data : *{data[4]}*\nID Digipos: *{data[0]}*\nNama: *{data[1]}*\nStatus : {data[2]}\nFisik: *{data[3]}*\n'
        # Show the Omset Data Outlet
        omset = get_omset(outlet_id)
        for data_omset in omset:
            locale.setlocale(locale.LC_ALL, '')
            trx = data_omset[0]
            rev = data_omset[2]
            Mom_trx = data_omset[1]
            Mom_rev = data_omset[3]
            formatted_rev = locale.format_string("%.3f", rev, grouping=True).rstrip('0').rstrip(',')
            reply_message += f'\n\n*TOTAL OMSET*\nTransaksi: {trx}\nMoM : {Mom_trx : .2f}%\n\nRevenue: {formatted_rev}\nMoM : {Mom_rev : .2f}%'
        # Show the Renewal Data Outlet
        renewal = get_renewal(outlet_id)
        for data_renewal in renewal:
            trx_renewal = data_renewal[0]
            rev_renewal = data_renewal[2]
            Mom_trx_renewal = data_renewal[1]
            Mom_rev_renewal = data_renewal[3]
            formatted_rev_renewal = locale.format_string("%.3f", rev_renewal, grouping=True).rstrip('0').rstrip(',')
            reply_message += f'\n\n*RENEWAL*\nTransaksi: {trx_renewal}\nMoM : {Mom_trx_renewal : .2f}%\n\nRevenue: {formatted_rev_renewal}\nMoM : {Mom_rev_renewal: .2f}%'
        
        # Show the CVM Data Outlet
        cvm = get_cvm(outlet_id)
        for data_cvm in cvm:
            trx_cvm = data_cvm[0]
            rev_cvm = data_cvm[2]
            Mom_trx_cvm = data_cvm[1]
            Mom_rev_cvm = data_cvm[3]
            formatted_rev_cvm = locale.format_string("%.3f", rev_cvm, grouping=True).rstrip('0').rstrip(',')
            reply_message += f'\n\n*CVM*\nTransaksi: {trx_cvm}\nMoM : {Mom_trx_cvm : .2f}%\n\nRevenue : {formatted_rev_cvm}\nMoM : {Mom_rev_cvm : .2f}%'
        bot.reply_to(message, reply_message, parse_mode='Markdown')
    else:
        bot.reply_to(message, "Outlet ID tidak ditemukan.\nSilahkan masukkan Outlet ID yang benar.")
    
    

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




# Initialize dictionaries to store registration data and status
user_search_data = {}
user_registration_data = {}
search_status = {}
registration_status = {}
print('Bot start running')
# Start polling
bot.polling()

# Close database connection
db.close()