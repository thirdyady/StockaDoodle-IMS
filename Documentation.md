# Project Milestones (Stockadoodle IMS API) 

## Members
1. [Gerfel Jay Jimenez](https://github.com/stultumJay)
2. [Kent Xylle Ryz J. Romarate](https://github.com/Romarate18)
3. [Noel Jose C. Villalveto](https://github.com/thirdyady)
4. [Ivan Risan Llenares](https://github.com/20230027589-cyber)

## System Overview

### Basic Operations
- **Retailers**:  
  Use the POS module to record sales. Product stocks update automatically after each transaction. Includes gamification (daily quota & streaks).

- **Managers**:  
  View visual sales dashboards (Bar & Pie charts), perform stock maintenance, and receive low-stock or expiration alerts.

- **Admins**:  
  Manage user accounts and maintain database integrity. Use Multi-Factor Authentication (MFA) for enhanced security.

---

## Information Needs (Reports)

The system generates the following reports:
1. **Sales Performance Report**
2. **Category Distribution Report**
3. **Retailer Performance Report**
4. **Low-Stock and Expiration Alert Report**
5. **Managerial Activity Log Report**
6. **Detailed Sales Transaction Report**
7. **User Accounts Report**

---

## Project Milestones

### **Milestone 1 (Nov Week 1): Project Setup & API Design**
**What we'll do:**  
Set up the project repository, define system scope, and identify key entities for StockaDoodle’s API.

**Deliverables:**  
- Completed `README.md` with team details and milestones  
- Defined problem statement and data model outline  
- Created basic Flask REST API folder structure
- Added the final hierarchy structure for the project for both API and App
- Added the applications logo in the icons directory


**Checklists:**  
- [ ] Hold team meeting to finalize topic  
- [ ] Define database models (Products, Users, Sales, Logs)  
- [ ] Set up `app.py` for Flask  
- [ ] Commit and push to GitHub  

---

### **Milestone 2 (Nov Week 2): Database & Endpoints**
**What we'll do:**  
Develop initial SQLite database schema and implement CRUD endpoints for Products and Users.

**Deliverables:**  
- `database.db` file created  
- Endpoints for `/products` and `/users`  
- Documentation of each endpoint in `api.yaml`

**Checklists:**  
- [ ] Create models and database connection  
- [ ] Implement POST, GET, PUT, DELETE routes  
- [ ] Test endpoints using Postman  
- [ ] Commit and push to GitHub  

---

### **Milestone 3 (Nov Week 3): Core System & Logging**
**What we'll do:**  
Implement core backend services, centralized logging, and inventory management features.

**Deliverables:**  
- ActivityLogger for product actions and API activity  
- InventoryManager with FEFO stock management
- MFA Service for secure multi-factor authentication
- UserManager for authentication, role-based access, and CRUD
-Initialize all models (category, product, sale, user, stock_batch, api_activity_log, product_log, retailer_metrics)

**Checklists:**  
- [ ] Add ActivityLogger methods for product and API audit trails
- [ ] Implement FEFO logic and stock validation in InventoryManager
- [ ] Add MFA generation, verification, and expiry tracking
- [ ] Implement UserManager with authentication, roles, and permission checks
- [ ] Create database models and initialize tables in app.py
- [ ] Commit and push updates

---

### **Milestone 4 (Nov Week 4): Routes, Reports & Notifications**
**What we'll do:**  
Build API routes, integrate core services, and implement reporting and notification features.

**Deliverables:**  
- CRUD routes for category, products, sales, users, and logs
- SalesManager for atomic sales, gamification, and retailer metrics
- ReportGenerator for all 7 required reports (sales, categories, retailer performance, low-stock alerts, etc.)
- NotificationService for automated email alerts (low-stock and expiring batches)
- Register all blueprints in app.py

**Checklists:**  
- [ ] Implement and test CRUD routes for all entities (category, products, sales, users, logs)
- [ ] Integrate SalesManager with FEFO inventory deductions and performance tracking
- [ ] Add report generation functionality and verify outputs
- [ ] Set up NotificationService for automated alerts
- [ ] Register all routes in app.py
- [ ] Commit and push updates

---

### **Milestone 5 (Dec Week 1): Final Integration & Documentation**
**What we'll do:**  
Finalize UI integration (if applicable) and ensure all APIs are functional and documented.

**Deliverables:**  
- Completed documentation (README, API, screenshots)  
- Stable final API release  
- Submission-ready project  

**Checklists:**  
- [ ] Merge all branches  
- [ ] Review code consistency  
- [ ] Write final documentation  
- [ ] Submit repository link on Moodle  

---
