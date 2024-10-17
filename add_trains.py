import sqlite3

def add_train_data():
    conn = sqlite3.connect('railway_reservation.db')
    cursor = conn.cursor()

    # Sample train data
    trains = [
        ('12345', 'Express Line', 'City A', 'City B', 100),
        ('67890', 'Fast Track', 'City C', 'City D', 150),
        ('54321', 'Night Rider', 'City E', 'City F', 200),
        ('09876', 'Morning Star', 'City G', 'City H', 120)
    ]

    # Insert train data into the trains table
    cursor.executemany('''
        INSERT INTO trains (train_number, train_name, source, destination, total_seats)
        VALUES (?, ?, ?, ?, ?)
    ''', trains)

    conn.commit()
    conn.close()
    print("Train data added successfully.")

if __name__ == "__main__":
    add_train_data()