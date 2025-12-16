<<div align="center">

  <h1>Stockadoodle - Inventory Management System</h1>
  
  <img src="desktop_app/assets/icons/stockadoodle-transparent.png" alt="Stockadoodle Logo" width="200" style="display: block; margin: auto;">
  
  <br>
  
  <i>Simplifying inventory management for convenience stores, one transaction at a time.</i>
  
</div>

<div align="center">

  ![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)
  ![PyQt6 Framework](https://img.shields.io/badge/PyQt6-Framework-green.svg)
  ![Flask API](https://img.shields.io/badge/Flask-API-lightgrey.svg)
  ![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=plastic&logo=mongodb&logoColor=white)
  ![Status maintained](https://img.shields.io/badge/status-maintained-brightgreen.svg)

</div>


## Overview

StockaDoodle is an inventory management system specifically designed for QuickMart Convenience Stores to streamline daily operations across multiple branches. Each branch operates its own independent server, ensuring that all data—including product inventory, sales records, and user activities—is stored locally for maximum security and reliability.

This decentralized approach allows three types of users to perform their duties efficiently:

- 👨‍💼 **Admins**: Manage user accounts and system settings
- 📊 **Managers**: Monitor stock levels, generate reports, and maintain inventory
- 🛒 **Retailers**: Process sales through the Point-of-Sale (POS) system



## Why StockaDoodle?

### Our Motivation

Small to medium-sized convenience stores often struggle with:

- Manual inventory tracking prone to errors
- Lack of real-time stock visibility
- Difficulty in generating sales reports
- No unified system for multiple branches


### Problem We Solve

StockaDoodle eliminates these pain points by providing:

- Automated inventory tracking
- Real-time stock level monitoring
- Instant sales reporting with visual analytics
- Secure, role-based access control
- Low-stock and expiration alerts


### What Makes Us Stand Out

- **Decentralized Architecture**: Each branch maintains its own data for security and independence
- **Gamification**: Retailers get motivated through daily quotas and streak tracking
- **Multi-Factor Authentication**: Enhanced security for sensitive operations



## Key Features

### For Retailers 🛒

- Point-of-Sale (POS) Module: Quick and easy transaction processing
- Automatic Stock Updates: Inventory adjusts automatically after each sale
- Gamification System: Daily sales quotas and streak tracking to boost motivation

### For Managers 📊

- Visual Dashboards: Bar charts and pie charts for sales analysis
- Stock Maintenance: Add, update, or remove products easily
- Smart Alerts: Get notified about low-stock items and upcoming expirations
- Comprehensive Reports: Sales performance, category distribution, and more

### For Admins 👨‍💼

- User Management: Create, modify, and deactivate user accounts
- Role Assignment: Control access levels (Admin/Manager/Retailer)
- Enhanced Security: Multi-Factor Authentication (MFA) for critical operations
- Activity Logs: Track all system activities for security and auditing



## Technologies Used

### Backend

- Flask: RESTful API server
- MongoEngine: Database ORM
- MongoDB: Lightweight, serverless database

### Frontend

- PyQt6: Modern desktop application framework
- Matplotlib/PyQtGraph: Data visualization
- Requests: HTTP client for API communication

### Development Tools

- Git/GitHub: Version control and collaboration
- Postman: API testing
- Python 3.9+: Core programming language


## Getting Started

### Installation

Follow these simple steps to set up StockaDoodle on your computer:

**Step 1: Download the Project**

```bash
# Clone the repository
git clone https://github.com/stultumJay/StockaDoodle-IMS.git

# Navigate to the project folder
cd StockaDoodle-IMS
```

**Step 2: Set Up the Backend (Server)**

```bash
# Go to the API server folder
cd api_server

# Install required packages
pip install -r requirements.txt

# Start the server
python app.py
```

What to expect: You'll see a message like "Running on http://127.0.0.1:5000" - this means your server is ready! ✅

**Step 3: Set Up the Frontend (Application)**

Open a new terminal window (keep the server running!) and:

```bash
# Go to the desktop app folder
cd ../desktop_app

# Install required packages
pip install -r requirements.txt

# Start the application
python main.py
```

What to expect: The StockaDoodle login window will appear on your screen! 🎉

### Running the Application

Every time you want to use StockaDoodle:

1. Start the Server First
   - Open a terminal
   - Go to api_server folder
   - Run `python app.py`
   - Wait for "Running on..." message

2. Then Start the Application
   - Open another terminal
   - Go to desktop_app folder
   - Run `python main.py`
   - Log in with your credentials

**Tip**: Keep both terminal windows open while using StockaDoodle. Closing them will stop the application.

### For Retailers

1. **Processing a Sale**
   - Log in with your Retailer account
   - Search for products using the search bar
   - Add items to the cart
   - Enter quantity
   - Click "Complete Sale"
   - View your daily progress and streaks!

2. **Viewing Your Performance**
   - Check your sales quota progress
   - See your streak count
   - View sales history


### For Managers

1. **Managing Inventory**
   - Navigate to "Inventory Management"
   - Add new products with details (name, price, stock, expiry date)
   - Update existing products
   - Remove discontinued items

2. **Viewing Reports**
   - Go to "Reports" section
   - Select report type (Sales, Category, Performance, etc.)
   - Choose date range
   - View and download data

3. **Monitoring Alerts**
    - Low-stock warnings
    - Products nearing expiration


### For Admins

1. **Managing Users**
   - Go to "User Management"
   - Click "Add New User"
   - Fill in details and assign role

2. **Viewing Security Logs**
   - Navigate to "Activity Logs"
   - Filter action type
   - Export logs for auditing

## User Roles & Permissions

| Feature                  | Retailer | Manager | Admin |
|--------------------------|----------|---------|-------|
| Process Sales (POS)      | ✅       | ✅      | ✅     |
| View Own Sales History   | ❌       | ✅      | ✅     |
| Manage Inventory         | ❌       | ✅      | ✅     |
| Generate Reports         | ❌       | ✅      | ✅     |
| View All Sales Data      | ❌       | ✅      | ✅     |
| Manage Users             | ❌       | ❌      | ✅     |
| Access Security Logs     | ❌       | ❌      | ✅     |

## 📊 Reports & Analytics

StockaDoodle generates comprehensive reports to help you make informed decisions:

1. Sales Performance Report: Track revenue, transactions, and trends over time
2. Category Distribution Report: See which product categories sell the most
3. Retailer Performance Report: Compare sales performance across different retailers
4. Low-Stock Alert Report: Identify products that need restocking
5. Expiration Alert Report: Monitor products approaching expiry dates
6. Activity Log Report: Security and audit trail of all system activities
7. Detailed Transaction Report: Complete breakdown of individual sales




## Project Structure

```plaintext
└── stultumjay-stockadoodle-ims/
    ├── README.md
    ├── __init__.py
    ├── Documentation.md
    ├── requirements.txt
    ├── Stockadoodle-api-docs.yaml
    │
    ├── api_server/                      # Backend (Flask API)
    │   ├── __init__.py
    │   ├── app.py                       # Main Flask application
    │   ├── config.py                    # Configuration settings
    │   ├── counters_init.py             # Script for initializing counters
    │   ├── requirements.txt             # Backend dependencies
    │   │
    │   ├── core/                        # Core Business Logic Services
    │   │   ├── __init__.py
    │   │   ├── activity_logger.py       # Logs all major system activities/transactions
    │   │   ├── inventory_manager.py     # Handles product, category, and stock batch management
    │   │   ├── mfa_service.py           # Multi-factor authentication logic
    │   │   ├── notification_service.py  # Handles system notifications/alerts
    │   │   ├── pdf_report_generator.py  # Generates detailed PDF reports
    │   │   ├── report_generator.py      # Generates various data reports
    │   │   ├── sales_manager.py         # Handles sales transactions and processing
    │   │   └── user_manager.py          # Handles user authentication and user profile management
    │   │
    │   ├── models/                      # Database Models (SQLAlchemy)
    │   │   ├── __init__.py
    │   │   ├── api_activity_log.py
    │   │   ├── base.py
    │   │   ├── category.py
    │   │   ├── product.py
    │   │   ├── product_log.py
    │   │   ├── retailer_metrics.py
    │   │   ├── sale.py
    │   │   ├── stock_batch.py
    │   │   └── user.py
    │   │
    │   ├── routes/                      # API Endpoints (Blueprints)
    │   │   ├── __init__.py
    │   │   ├── category.py
    │   │   ├── dashboard.py
    │   │   ├── logs.py
    │   │   ├── metrics.py
    │   │   ├── notifications.py
    │   │   ├── products.py
    │   │   ├── reports.py
    │   │   ├── sales.py
    │   │   └── users.py
    │   │
    │   └── utils/                       # Backend Utility Functions
    │       ├── __init__.py
    │       ├── counters.py
    │       ├── helpers.py
    │       └── pdf_styles.py
    │
    └── desktop_app/                     # Frontend (PyQt6 Desktop Application)
        ├── __init__.py
        ├── main.py                      # Application entry point
        ├── requirements.txt             # Frontend dependencies
        │
        ├── api_client/                  # API Communication Layer
        │   └── stockadoodle_api.py      # Wrapper for backend API calls
        │
        ├── assets/                      # Static Assets (Fonts and Icons)
        │   ├── fonts/
        │   │   ├── Inter-Bold.ttf
        │   │   ├── Inter-Light.ttf
        │   │   ├── Inter-Medium.ttf
        │   │   └── Inter-Regular.ttf
        │   └── icons/                   # UI icons
        │
        ├── services/
        │   └── report_generator.py      # Frontend-specific report generation service
        │
        ├── ui/                          # User Interface Components and Views
        │   ├── __init__.py
        │   ├── header_bar.py
        │   ├── login_window.py
        │   ├── main_window.py
        │   ├── mfa_window.py
        │   ├── side_bar.py
        │   ├── splash_screen.py
        │   │
        │   ├── components/              # Reusable UI Elements
        │   │   ├── __init__.py
        │   │   ├── add_batch_dialog.py
        │   │   ├── batch_dispose_dialog.py
        │   │   ├── category_form_dialog.py
        │   │   ├── confirm_delete_dialog.py
        │   │   ├── custom_tab_widget.py
        │   │   ├── edit_batch_dialog.py
        │   │   ├── loading_spinner.py
        │   │   ├── modern_card.py
        │   │   ├── product_card.py
        │   │   └── stock_batch_selector.py
        │   │
        │   ├── pages/                   # Main Application Pages
        │   │   ├── __init__.py
        │   │   ├── activity.py
        │   │   ├── administration.py
        │   │   ├── alerts.py
        │   │   ├── dashboard.py
        │   │   ├── profile.py
        │   │   └── products/
        │   │       ├── __init__.py
        │   │       ├── product_detail.py
        │   │       ├── product_form.py
        │   │       └── product_list.py
        │   │
        │   ├── profile/                 # Profile Management Views
        │   │   ├── __init__.py
        │   │   ├── activity_log_tab.py
        │   │   └── profile_page.py
        │   │
        │   ├── reports/
        │   │   └── reports_page.py
        │   │
        │   └── sales/                   # Sales Management Views
        │       ├── __init__.py
        │       ├── sales_management.py
        │       └── sales_records.py
        │
        └── utils/                       # Frontend Utility Functions
            ├── __init__.py
            ├── __main__.py
            ├── animations.py
            ├── api_wrapper.py
            ├── app_state.py
            ├── app_theme.py
            ├── config.py
            ├── helpers.py
            ├── icons.py
            ├── notifications.py
            ├── style_presets.py
            ├── styles.py
            ├── theme.py
            └── validators.py
```


## Development Team

### Meet the Team Behind StockaDoodle

|                                                                 |                                                                 |                                                                 |                                                                 |
|-----------------------------------------------------------------|-----------------------------------------------------------------|-----------------------------------------------------------------|-----------------------------------------------------------------|
| <div style="text-align: center;"><br>![Gerfel Jay Jimenez](desktop_app/assets/icons/jimenez.png)<br><br></div><div style="text-align: left;"><br>**Gerfel Jay Jimenez**<br>**Project Leader & Lead Backend Developer**<br>20230028267@my.xu.edu.ph<br>BS Information Technology<br><br>**Primary Contributions:**<br>• Project Manager overseeing timeline and coordination<br>• Backend development and architecture design<br>• API endpoint implementation<br>• Database management and optimization<br><br>**Key Skills:**<br>System Architecture, API Development, Database Management (MySQL, SQLite, MongoDB), Project Management, Git/GitHub<br><br><a href="https://github.com/stultumJay">![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)</a><br><br></div> | <div style="text-align: center;"><br>![Ivan Risan Llenares](desktop_app/assets/icons/llenares.png)<br><br></div><div style="text-align: left;"><br>**Ivan Risan Llenares**<br>**Testing & Quality Assurance Analyst**<br>20230027589@my.xu.edu.ph<br>BS Information Technology<br><br>**Primary Contributions:**<br>• Comprehensive feature testing and validation<br>• Quality assurance protocols<br>• Bug tracking and resolution<br>• Integration testing coordination<br><br>**Key Skills:**<br>Software Testing, Quality Assurance, Bug Tracking, Test Case Development<br><br><a href="https://github.com/20230027589-cyber">![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)</a><br><br></div> | <div style="text-align: center;"><br>![Kent Xylle Ryz Romarate](desktop_app/assets/icons/romarate.png)<br><br></div><div style="text-align: left;"><br>**Kent Xylle Ryz Romarate**<br>**Documentation Lead**<br>20210022802@my.xu.edu.ph<br>BS Information Technology<br><br>**Primary Contributions:**<br>• Project documentation creation<br>• Technical writing and user manuals<br>• PowerPoint presentations<br>• Documentation structure design<br><br>**Key Skills:**<br>Documentation Writing, Technical Writing, PowerPoint Presentation, Project Communication, Research, Version Control (Git)<br><br><a href="https://github.com/Romarate18">![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)</a><br><br></div> | <div style="text-align: center;"><br>![Noel Jose Villalveto](desktop_app/assets/icons/villalveto.png)<br><br></div><div style="text-align: left;"><br>**Noel Jose Villalveto**<br>**Frontend UI/UX Developer**<br>20230028624@my.xu.edu.ph<br>BS Information Technology<br><br>**Primary Contributions:**<br>• Frontend interface design and implementation<br>• User experience optimization<br>• API Integration with UI<br>• Responsive design implementation<br><br>**Key Skills:**<br>Frontend Development (HTML, CSS, JavaScript), UI/UX Design, Responsive Design, User-Centered Design, Git/GitHub<br><br><a href="https://github.com/thirdyady">![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)</a><br><br></div> |

---

<div align="center">

⭐ If you find StockaDoodle helpful, please consider giving it a star!

Made with ❤️ by the StockaDoodle Team

</div>
