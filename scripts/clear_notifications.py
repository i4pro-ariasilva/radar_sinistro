import sqlite3

DB_PATH = 'database/radar_sinistro.db'

def clear_notifications():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM notificacoes_risco")
    conn.commit()
    conn.close()
    print("Todas as notificações foram removidas da tabela notificacoes_risco.")

if __name__ == "__main__":
    clear_notifications()
