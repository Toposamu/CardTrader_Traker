import os
import datetime

# Messaggio automatico per il commit
ora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
messaggio_commit = f"🔄 Aggiornamento automatico del {ora}"

# Comandi Git
os.system("git add .")
os.system(f'git commit -m "{messaggio_commit}"')
os.system("git push")
