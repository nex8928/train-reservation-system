# Import necessary libraries
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

# Database Configuration
def create_database():
    conn = sqlite3.connect('railway_reservation.db')
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Create Trains table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trains (
            train_id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_number TEXT UNIQUE NOT NULL,
            train_name TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            total_seats INTEGER NOT NULL
        )
    ''')
    
    # Create Reservations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            pnr_number TEXT PRIMARY KEY,
            user_id INTEGER,
            train_id INTEGER,
            journey_date TEXT NOT NULL,
            class_type TEXT NOT NULL,
            seat_number INTEGER NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (train_id) REFERENCES trains (train_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# User Authentication Class
class UserAuth:
    def __init__(self):
        self.conn = sqlite3.connect('railway_reservation.db')
        self.cursor = self.conn.cursor()
    
    def login(self, username, password):
        self.cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                          (username, password))
        return self.cursor.fetchone()
    
    def logout(self):
        # Implementation for logout functionality
        pass

# Flask Routes
app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_auth = UserAuth()
        user = user_auth.login(username, password)
        if user:
            flash('Login successful!', 'success')
            return redirect(url_for('post_login_options'))  # Redirect to options page
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/post_login_options')
def post_login_options():
    return render_template('post_login_options.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        email = request.form['email']
        
        try:
            conn = sqlite3.connect('railway_reservation.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, full_name, email)
                VALUES (?, ?, ?, ?)
            ''', (username, password, full_name, email))
            conn.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
        finally:
            conn.close()
    
    return render_template('register.html')

# Reservation System Class
class ReservationSystem:
    def __init__(self):
        self.conn = sqlite3.connect('railway_reservation.db')
        self.cursor = self.conn.cursor()

    def generate_pnr(self):
        """Generate a unique PNR number."""
        return f"PNR{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def check_seat_availability(self, train_id, journey_date, class_type):
        """Check if seats are available for a given train and date."""
        self.cursor.execute('''
            SELECT COUNT(*) FROM reservations
            WHERE train_id = ? AND journey_date = ? AND class_type = ? AND status = 'CONFIRMED'
        ''', (train_id, journey_date, class_type))
        booked_seats = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT total_seats FROM trains WHERE train_id = ?', (train_id,))
        total_seats = self.cursor.fetchone()[0]

        return total_seats - booked_seats

    def make_reservation(self, user_id, train_id, journey_date, class_type):
        """Make a reservation if seats are available."""
        available_seats = self.check_seat_availability(train_id, journey_date, class_type)
        if available_seats > 0:
            pnr = self.generate_pnr()
            seat_number = available_seats  # Assign the next available seat
            try:
                self.cursor.execute('''
                    INSERT INTO reservations 
                    (pnr_number, user_id, train_id, journey_date, class_type, seat_number, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (pnr, user_id, train_id, journey_date, class_type, seat_number, 'CONFIRMED'))
                self.conn.commit()
                return pnr
            except Exception as e:
                self.conn.rollback()
                print(f"Error making reservation: {e}")
                return None
        else:
            print("No seats available")
            return None

    def close(self):
        """Close the database connection."""
        self.conn.close()

# Cancellation System Class
class CancellationSystem:
    def __init__(self):
        self.conn = sqlite3.connect('railway_reservation.db')
        self.cursor = self.conn.cursor()
    
    def get_booking_details(self, pnr_number):
        self.cursor.execute('''
            SELECT r.*, t.train_name, t.train_number 
            FROM reservations r 
            JOIN trains t ON r.train_id = t.train_id 
            WHERE r.pnr_number = ?
        ''', (pnr_number,))
        return self.cursor.fetchone()
    
    def cancel_ticket(self, pnr_number):
        try:
            self.cursor.execute('UPDATE reservations SET status = ? WHERE pnr_number = ?', 
                              ('CANCELLED', pnr_number))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            return False

# New Route to Fetch Train Name
@app.route('/get_train_name')
def get_train_name():
    train_number = request.args.get('train_number')
    conn = sqlite3.connect('railway_reservation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT train_name FROM trains WHERE train_number = ?', (train_number,))
    train = cursor.fetchone()
    conn.close()
    if train:
        return {'train_name': train[0]}
    else:
        return {'train_name': None}

# New Route for Reservation
@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        user_id = 1  # Replace with actual user ID from session or login
        train_number = request.form['trainNumber']
        journey_date = request.form['journeyDate']
        class_type = request.form['classType']
        
        # Fetch train_id using train_number
        conn = sqlite3.connect('railway_reservation.db')
        cursor = conn.cursor()
        cursor.execute('SELECT train_id FROM trains WHERE train_number = ?', (train_number,))
        train = cursor.fetchone()
        conn.close()
        
        if train:
            train_id = train[0]
            reservation_system = ReservationSystem()
            pnr = reservation_system.make_reservation(user_id, train_id, journey_date, class_type)
            reservation_system.close()
            
            if pnr:
                flash(f'Reservation successful! Your PNR is {pnr}', 'success')
            else:
                flash('Reservation failed. Please try again.', 'danger')
        else:
            flash('Train not found.', 'danger')
    
    return render_template('reservation.html')

# New Route for Cancellation
@app.route('/cancel', methods=['GET', 'POST'])
def cancel():
    reservation = None
    if request.method == 'POST':
        pnr_number = request.form['pnr']
        conn = sqlite3.connect('railway_reservation.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.pnr_number, r.journey_date, r.class_type, r.seat_number, t.train_name, t.train_number
            FROM reservations r
            JOIN trains t ON r.train_id = t.train_id
            WHERE r.pnr_number = ? AND r.status = 'CONFIRMED'
        ''', (pnr_number,))
        reservation = cursor.fetchone()
        conn.close()
        if reservation:
            reservation = {
                'pnr_number': reservation[0],
                'journey_date': reservation[1],
                'class_type': reservation[2],
                'seat_number': reservation[3],
                'train_name': reservation[4],
                'train_number': reservation[5]
            }
        else:
            flash('No confirmed reservation found for this PNR.', 'danger')
    return render_template('cancellation.html', reservation=reservation)

@app.route('/confirm_cancellation', methods=['POST'])
def confirm_cancellation():
    pnr_number = request.form['pnr']
    try:
        conn = sqlite3.connect('railway_reservation.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE reservations SET status = ? WHERE pnr_number = ?', ('CANCELLED', pnr_number))
        conn.commit()
        flash('Reservation cancelled successfully.', 'success')
    except Exception as e:
        conn.rollback()
        flash('Error cancelling reservation.', 'danger')
    finally:
        conn.close()
    return redirect(url_for('cancel'))

# Main Application
def main():
    # Create database and tables
    create_database()
    
    # Start the application with login window
    app.run(debug=True)

if __name__ == "__main__":
    main()