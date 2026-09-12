from database.fetch import get_flagged_transactions


def print_summary():

    rows = get_flagged_transactions()

    print()

    print("=" * 60)

    print("SUMMARY")

    print("=" * 60)

    print("Flagged Transactions :", len(rows))

    total_loss = 0

    for row in rows:

        total_loss += row["amount"]

    print("Prevented Loss : ₹", total_loss)

    print("=" * 60)