import sqlite3

def tokens_update():
    conn = sqlite3.connect('static/ledger.db')
    conn.text_factory = str
    c = conn.cursor()

    tok = sqlite3.connect('tokens.db')
    tok.text_factory = str
    t = tok.cursor()
    t.execute("CREATE TABLE IF NOT EXISTS transactions (block_height INTEGER, timestamp, token, address, recipient, amount INTEGER)")
    tok.commit()

    t.execute("SELECT block_height FROM transactions ORDER BY block_height DESC LIMIT 1;")
    try:
        token_last_block = int(t.fetchone()[0])
    except:
        token_last_block = 0
    print("token_last_block", token_last_block)

    # print all token issuances
    c.execute("SELECT block_height, timestamp, address, recipient, openfield FROM transactions WHERE block_height > ? AND openfield LIKE ? AND reward = 0 ORDER BY block_height ASC;", (token_last_block,) + ("token:issue" + '%',))
    results = c.fetchall()
    print(results)

    tokens_processed = []

    for x in results:
        if x[4].split(":")[2].lower().strip() not in tokens_processed:
            block_height = x[0]
            print("block_height", block_height)

            timestamp = x[1]
            print("timestamp", timestamp)

            token = x[4].split(":")[2].lower().strip()
            tokens_processed.append(token)
            print("token", token)

            issued_by = x[3]
            print("issued_by", issued_by)

            total = x[4].split(":")[3]
            print("total", total)

            t.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?)", (block_height, timestamp, token, "issued", issued_by, total))
        else:
            print("issuance already processed:", x[1])

    tok.commit()
    # print all token issuances

    print("---")

    # print all transfers of a given token
    # token = "worthless"


    c.execute("SELECT openfield FROM transactions WHERE block_height > ? AND openfield LIKE ? and reward = 0 ORDER BY block_height ASC;", (token_last_block,) + ("token:transfer" + '%',))
    openfield_transfers = c.fetchall()

    tokens_transferred = []
    for transfer in openfield_transfers:
        if transfer[0].split(":")[2].lower().strip() not in tokens_transferred:
            tokens_transferred.append(transfer[0].split(":")[2].lower().strip())

    print("tokens_transferred",tokens_transferred)

    for token in tokens_transferred:
        print("processing", token)
        c.execute("SELECT block_height, timestamp, address, recipient, openfield FROM transactions WHERE block_height > ? AND openfield LIKE ? AND reward = 0 ORDER BY block_height ASC;", (token_last_block,) + ("token:transfer:" + token + ':%',))
        results2 = c.fetchall()
        print(results2)

        for r in results2:
            block_height = r[0]
            print("block_height", block_height)

            timestamp = r[1]
            print("timestamp", timestamp)

            token = r[4].split(":")[2]
            print("token", token, "operation")

            sender = r[2]
            print("transfer_from", sender)

            recipient = r[3]
            print("transfer_to", recipient)

            try:
                print (r[4])
                transfer_amount = int(r[4].split(":")[3])
            except:
                transfer_amount = 0

            print("transfer_amount", transfer_amount)

            # calculate balances
            t.execute("SELECT sum(amount) FROM transactions WHERE recipient = ? AND block_height < ? AND token = ?", (sender,) + (block_height,) + (token,))
            try:
                credit_sender = int(t.fetchone()[0])
            except:
                credit_sender = 0
            print("credit_sender", credit_sender)

            t.execute("SELECT sum(amount) FROM transactions WHERE address = ? AND block_height <= ? AND token = ?", (sender,) + (block_height,) + (token,))
            try:
                debit_sender = int(t.fetchone()[0])
            except:
                debit_sender = 0
            print("debit_sender", debit_sender)
            # calculate balances

            # print all token transfers
            balance_sender = credit_sender - debit_sender
            print("balance_sender", balance_sender)

            if balance_sender - transfer_amount >= 0 or transfer_amount < 0:
                t.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?)", (block_height, timestamp, token, sender, recipient, transfer_amount))
            else:
                print("invalid transaction by", sender)
            print("---")

        tok.commit()

    conn.close()

