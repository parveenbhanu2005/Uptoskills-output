from database.database import get_connection


def get_all_transactions():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("SELECT * FROM transactions")

    rows = cur.fetchall()

    conn.close()

    return rows


def get_flagged_transactions():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("SELECT * FROM flagged_transactions")

    rows = cur.fetchall()

    conn.close()

    return rows


def get_user_history(user_id):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""

    SELECT *

    FROM transactions

    WHERE user_id=?

    ORDER BY timestamp

    """,(user_id,))

    rows = cur.fetchall()

    conn.close()

    return rows