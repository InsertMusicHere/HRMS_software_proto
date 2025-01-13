# Employee Leave Management System 🏢📋

This **Employee Leave Management System** is a Flask-based web application designed to manage employee leave requests and attendance efficiently. With features like user authentication, leave balance tracking, leave approvals, and attendance data export, this system is a robust tool for HR and management.

---

## 🌟 **Features**
### 1. **User Authentication**
   - Secure login system with session management.
   - Displays personalized dashboard based on user roles.

### 2. **Employee Dashboard**
   - **Profile Information**: Displays employee details and profile picture.
   - **Leave Balances**: Tracks casual, emergency, and medical leave balances.
   - **Pending Leaves**: Shows leave requests awaiting approval.

### 3. **Leave Management**
   - **Apply for Leaves**: Employees can apply for different types of leaves.
   - **Approve/Decline Leaves**: Managers can review and approve/reject leave requests.

### 4. **Attendance Management**
   - **CSV Export**: Exports attendance data to a downloadable CSV file.
   - Automatically formats timestamps and organizes data for reporting.

### 5. **Role-Based Access**
   - **Employees**: View balances and apply for leaves.
   - **Managers**: Approve or decline leave requests from reporting employees.

---

## 🚀 **Technologies Used**
- **Backend Framework:** Flask
- **Database:** MongoDB (via PyMongo)
- **Frontend:** HTML, CSS, Jinja2 templates
- **Utilities:**
  - **Pandas:** For data manipulation and CSV export.
  - **Flask-Session:** For session management.
  - **Flask-Flash:** For notifications.

---

## 📚 **App Routes**
### 1. **Home Page (`/`)**
   - Displays a welcome message or prompts the user to log in.
   - Renders `landing_page.html`.

### 2. **Login (`/login`)**
   - Authenticates users based on their Employee ID and password.
   - Redirects to the dashboard on successful login.

### 3. **Dashboard (`/logged_in`)**
   - Displays employee details, leave balances, and pending leaves for managers.
   - Renders `logged_in.html`.

### 4. **Leave Management**
   - **View Leaves (`/leaves`)**: Displays leave balances and pending leave requests.
   - **Approve Leave (`/approve_leave`)**: Approves a leave request and updates the database.
   - **Decline Leave (`/decline_leave`)**: Rejects a leave request and updates the leave balance.

### 5. **Attendance Data Export**
   - **Generate CSV (`/generate_csv`)**: Exports attendance data as a CSV file for easy reporting.

---

## 🛠️ **Getting Started**

### Prerequisites
- Python 3.8 or later
- MongoDB database
- Virtual environment (optional but recommended)

### Installation
1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/employee-leave-management.git
   cd employee-leave-management
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   Create a .env file in the root directory with the following
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   MONGO_URI=mongodb://localhost:27017/your_database_name

   flask run

🧩 Folder Structure
```
  employee-leave-management/
      ├── static/           # CSS, JavaScript, and images
      ├── templates/        # HTML templates for rendering views
      ├── app.py            # Main application file
      ├── utils.py          # Utility functions (e.g., CSV generation)
      ├── requirements.txt  # List of Python dependencies
      └── .env              # Environment variables

