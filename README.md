# Enterprise Tender & Bid Management System

A comprehensive, full-stack web application designed to streamline the entire procurement lifecycle. From vendor registration and tender creation to bid submission, evaluation, and purchase order generation, this system provides a secure, role-based platform for efficient supply chain management.

## 🚀 Key Features

*   **Comprehensive User Authentication:** Secure login, registration, and password management for all user types.
*   **Role-Based Access Control (RBAC):** 4 distinct roles (Admin, Procurement Officer, Manager, Vendor) with tailored dashboards, permissions, and routing.
*   **Vendor Onboarding & Compliance:** Vendors can register and upload mandatory compliance documents (GST, PAN, Trade License).
*   **Document Verification Workflow:** Multi-step approval process where Managers/Admins review vendor documents. Includes rejection feedback and strict retry limits for uploads.
*   **Tender Lifecycle Management:** Complete end-to-end management (Draft -> Pending Approval -> Open -> Evaluation -> Closed -> Cancelled).
*   **Tender Publishing:** Create rich-text tenders with document attachments, categories, terms & conditions, and deadlines.
*   **Secure Bid Management:** Vendors can securely submit bids with pricing and compliance docs. Bids remain sealed/hidden until the tender closing date.
*   **Multi-Stage Evaluation System:** Built-in technical and financial scoring for bids, automatic rank assignment based on total scores, and manager approval workflows.
*   **Purchase Order Automation:** One-click automated purchase order generation for winning bids.
*   **PO Fulfillment Workflow:** Track POs from Draft -> Approved -> Dispatched (Vendor) -> Delivered with Proof of Delivery (Vendor) -> Completed.
*   **Analytics Dashboard:** Visual representation of monthly spends, tender status, and PO statuses using dynamic Chart.js integrations.
*   **In-System Messaging:** Direct communication channel between Vendors and Admins, including automated "Document Limit Reset" requests.
*   **Audit Trail & System Logs:** Comprehensive tracking of all critical system events (user logins, approvals, PO generation, dispatch, etc.) for high-level accountability.
*   **Vendor E-Agreement:** Vendors must digitally sign and agree to Purchase Order terms before they are allowed to dispatch goods.
*   **Real-time & Email Notifications:** Automated in-app notifications and SMTP email alerts for tender updates, bid status, PO receipts, and profile verification.
*   **Advanced Data Security:** Strict file upload validation with **AI File Scanning**, secure document storage, **File Upload Rate Limiting** to prevent spam, and robust password hashing.
*   **Data Export (Excel):** Export system reports, vendor lists, and financial data directly into Excel sheets for offline analysis.
*   **Google OAuth Integration:** Seamless, one-click sign-in experience using Google credentials via `django-allauth`.
*   **Responsive Modern UI:** Built with Tailwind CSS, featuring full Light and Dark mode support, micro-animations, and Lucide icons for a premium user experience.

## 🛠️ Technology Stack

*   **Backend:** Python, Django
*   **Frontend:** HTML5, Tailwind CSS, Vanilla JavaScript, Lucide Icons
*   **Database:** PostgreSQL
*   **Authentication:** Django Auth, Django-Allauth (Google OAuth2)
*   **Deployment:** Vercel (Web Hosting), Render (Database Hosting)

## 📂 Folder Structure

```text
Tender-Bid-Management/
├── apps/                       # Django Applications
│   ├── accounts/               # User models, authentication, roles, system logs
│   ├── vendors/                # Vendor profiles, document verification
│   ├── tenders/                # Tender models, publishing logic
│   ├── bids/                   # Bid submissions, pricing, vendor documents
│   ├── evaluations/            # Bid scoring, technical/financial review
│   ├── purchase_orders/        # PO generation, status tracking
│   ├── notifications/          # System alerts and notifications
│   └── reports/                # System analytics and reporting
├── config/                     # Core Django Configuration
│   ├── settings/               # Environment settings (base, development, production)
│   ├── urls.py                 # Main URL routing
│   └── wsgi.py                 # WSGI config for Vercel
├── static/                     # Static Assets
│   ├── css/                    # Tailwind output & custom styles
│   └── js/                     # Client-side interactivity
├── templates/                  # HTML Templates
│   ├── base.html               # Master layout
│   ├── accounts/               # Auth templates
│   ├── dashboard/              # Role-specific dashboards
│   └── ...                     # App-specific templates
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
└── vercel.json                 # Vercel deployment configuration
```

## ⚙️ Local Setup & Installation

Follow these steps to set up the project locally for development.

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/Tender-Bid-Management.git
cd Tender-Bid-Management
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the root directory and add your configurations:
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/tender_db
```

### 5. Database Setup
Apply the migrations to set up the database schema:
```bash
python manage.py migrate
```

### 6. Create Superuser
Create an admin account to access the backend:
```bash
python manage.py create_superuser
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000` in your browser.

## 🔄 System Workflow

1.  **Registration:** Vendors register on the platform and submit their company details and verification documents.
2.  **Verification:** Procurement Officers review and approve vendor profiles.
3.  **Tender Creation:** Managers/Officers create tenders specifying requirements, categories, and deadlines.
4.  **Bidding:** Approved vendors view active tenders and submit their bids (technical details + financial quotes) before the deadline.
5.  **Evaluation:** After the deadline, the evaluation committee reviews the bids, assigns scores, and selects a winner based on the criteria.
6.  **Award & PO:** The winning bid is approved, and a Purchase Order is automatically generated and sent to the vendor.

## Devloped by
Nishit Bhavsar
