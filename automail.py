import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime
from pypdf import PdfReader  

# ΛΟΓΑΡΙΑΣΜΟΥ & ΦΑΚΕΛΩΝ ---
EMAIL_ACCOUNT = ""  
EMAIL_PASSWORD = ""     
BASE_SAVE_FOLDER = "Taxinomimena_Eggrafa"  # Ο κεντρικός φάκελος αποθήκευσης

# 🎯 ΕΔΩ ΟΡΙΖΕΙΣ ΤΟΥΣ ΦΑΚΕΛΟΥΣ ΚΑΙ ΤΑ KEYWORDS ΠΟΥ ΨΑΧΝΕΙΣ
 CATEGORIES = {
    # 📱 Λογαριασμοί χωρισμένοι ανά εταιρεία
    "cosmote": os.path.join(BASE_SAVE_FOLDER, "Logariasmoi", "Cosmote"),
    "vodafone": os.path.join(BASE_SAVE_FOLDER, "Logariasmoi", "Vodafone"),
    "nova": os.path.join(BASE_SAVE_FOLDER, "Logariasmoi", "Nova"),
    "δεη": os.path.join(BASE_SAVE_FOLDER, "Logariasmoi", "DEH"),
 } 
    # 📑 Άλλες κατηγορίες εγγράφων
    "τιμολόγιο": os.path.join(BASE_SAVE_FOLDER, "Timologia"),
    "συμφωνητικό": os.path.join(BASE_SAVE_FOLDER, "Symbaseis")
    

DEFAULT_FOLDER = os.path.join(BASE_SAVE_FOLDER, "Diafora_Eggrafa")  # Αν δεν βρει καμία λέξη

# Δημιουργία φακέλων στο PC
for folder in CATEGORIES.values():
    os.makedirs(folder, exist_ok=True)
os.makedirs(DEFAULT_FOLDER, exist_ok=True)

# --- 2. ΣΥΝΔΕΣΗ ΜΕ ΤΟ GMAIL ---
print("🔄 Σύνδεση με το Gmail...")
mail = imaplib.IMAP4_SSL("imap.gmail.com")  # 👈 Διορθώθηκε για να μην βγάζει socket error!
mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
mail.select("inbox")

# 🎯 ΑΝΑΖΗΤΗΣΗ ΓΙΑ ΟΛΑ ΤΑ ΜΗ ΑΝΑΓΝΩΣΜΕΝΑ EMAIL (Χωρίς φίλτρο αποστολέα!)
status, data = mail.search(None, 'UNSEEN')
email_ids = data[0].split()

print(f"🎯 Βρέθηκαν {len(email_ids)} νέα μη αναγνωσμένα μηνύματα στο Inbox.")

# --- 3. ΕΠΕΞΕΡΓΑΣΙΑ EMAIL & PDF ---
for num in email_ids:
    status, email_data = mail.fetch(num, "(RFC822)")
    raw_email = email_data[0][1] 
    msg = email.message_from_bytes(raw_email)
    
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition") is None:
            continue
            
        filename = part.get_filename()
        
        if filename:
            decoded_filename = ""
            for part_str, encoding in decode_header(filename):
                if isinstance(part_str, bytes):
                    decoded_filename += part_str.decode(encoding or "utf-8", errors="ignore")
                else:
                    decoded_filename += part_str
            
            # Φιλτράρουμε αυστηρά ΜΟΝΟ τα αρχεία PDF
            if not decoded_filename.lower().endswith('.pdf'):
                continue
                
            tora = datetime.now()
            kathari_imerominia = tora.strftime("%Y-%m-%d_%H-%M")
            
            onoma, epektasi = os.path.splitext(decoded_filename)
            teliko_onoma = f"eggrapho_{kathari_imerominia}{epektasi}"
            
            # 1. Προσωρινή αποθήκευση στον κεντρικό φάκελο
            temp_path = os.path.join(BASE_SAVE_FOLDER, teliko_onoma)
            with open(temp_path, "wb") as f:
                f.write(part.get_payload(decode=True))
            
            # 2. 🔍 Σκανάρισμα του κειμένου μέσα στο PDF
            target_folder = DEFAULT_FOLDER  
            try:
                reader = PdfReader(temp_path)
                pdf_text = ""
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pdf_text += text.lower()  
                
                # Έλεγχος keywords
                for keyword, folder_path in CATEGORIES.items():
                    if keyword.lower() in pdf_text:
                        target_folder = folder_path
                        print(f"✨ Ανιχνεύθηκε keyword: '{keyword}' -> Φάκελος: {os.path.basename(folder_path)}")
                        break  
                        
            except Exception as e:
                print(f"❌ Αδυναμία ανάγνωσης περιεχομένου PDF: {e}")
            
            # 3. Μετακίνηση του αρχείου στον σωστό υποφάκελο
            final_filepath = os.path.join(target_folder, teliko_onoma)
            os.rename(temp_path, final_filepath)
            
            print(f"📥 Το έγγραφο αποθηκεύτηκε στο -> '{final_filepath}'")

mail.close()
mail.logout()
print("🔌 Η εργασία ολοκληρώθηκε!")
