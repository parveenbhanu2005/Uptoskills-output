from database.database import get_connection


def update_daily_metrics(date, prevented_loss):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""

    SELECT *

    FROM daily_metrics

    WHERE date=?

    """,(date,))

    row = cur.fetchone()

    if row is None:

        cur.execute("""

        INSERT INTO daily_metrics

        VALUES(?,?,?,?)

        """,(

            date,
            1,
            1,
            prevented_loss

        ))

    else:

        cur.execute("""

        UPDATE daily_metrics

        SET

        total_transactions = total_transactions + 1,

        fraud_transactions = fraud_transactions + 1,

        prevented_loss = prevented_loss + ?

        WHERE date=?

        """,(

            prevented_loss,
            date

        ))

    conn.commit()

    conn.close()


def get_metrics():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""

    SELECT *

    FROM daily_metrics

    ORDER BY date DESC

    """)

    rows = cur.fetchall()

    conn.close()

    return rows