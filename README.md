# Enterprise Tender & Bid Management System

## 🛠️ Project Setup & Installation (For New Users)
When you clone or download this project, follow these steps to set it up properly on your machine.

### Method 1: Automatic Setup (Windows Only)
Simply double-click the **`setup.bat`** file in the project directory. 
It will automatically:
1. Create a Python Virtual Environment (`venv`)
2. Activate it
3. Install all dependencies from `requirements.txt`
4. Apply database migrations

### Method 2: Manual Setup (All Systems)
1. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   ```
2. **Activate the Virtual Environment**:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
3. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run Database Migrations**:
   ```bash
   python manage.py migrate
   ```
5. **Start the Server**:
   ```bash
   python manage.py runserver
   ```

---

Aa document system na darek phase (tappe) ni sampurna mahiti aape che. System kevi rite kam kare che, konna su role che, ane ek tender create thava thi laine saaman aavi jay tya sudhi nu aakhu workflow ahia samjavva ma aavyu che.

---

## 👥 System Roles (Role-Based Access Control)
System ma total 4 main roles che:
1. **Admin**: System na malik. Darek user ne edit, active/inactive, ane system ni security manage kare.
2. **Procurement Officer**: Ground level nu kaam kare. Tender banave, Vendor nu verification kare, bids ne marks (score) aape ane PO banave.
3. **Manager**: Final Approval Authority. Procurement ae banavela Tender, Vendor verification, Bid award ane PO ne check kari ne final "Approve" ke "Reject" kare.
4. **Vendor**: Bahaar ni company je tender ma bhag le che. Potani profile banave, bid submit kare ane contract malse to saaman mokli ne delivery proof aape.

---

## 🚀 Development Phases & Workflow

### Phase 1 & 2: Base Foundation & Security
- **What it does:** System nu basic structure (Django + TailwindCSS) ane secure login system banaveli che. 
- **Workflow:** Koi pan user potana email ane password thi login kare. System auto-detect kare ke aa user no role su che ane aene aena role na Dashboard par redirect kare.

### Phase 3: Vendor Onboarding & Verification
- **What it does:** Nava vendor system ma joday tyaarni process.
- **Workflow:** 
  1. Vendor sign up kari ne potani Company details (GST, PAN, Address) nakhi ne verification mate mokle.
  2. **Procurement Officer** e details check kare ane "Verify" kare.
  3. **Manager** final "Approve" kare pachi j Vendor system ma "Active" thay ane bids ma bhag lai shake.

### Phase 4: Dashboards & Notifications
- **What it does:** Darek user ne potanu personalized dashboard ane real-time alerts.
- **Workflow:** System ma kai pan thay (jem ke navu tender aavu, bid winner thavu, PO aavu) to user ne upar ganteedi (bell icon) ma live notification aavi jay. 

### Phase 5: Tender Management & Bidding
- **What it does:** Main business process - Tenders bahar padva ane Vendors dwara bhav (bids) bharva.
- **Workflow:**
  1. **Procurement Officer** navu Tender banave (Budget, Deadline, Items) ane Manager ne mokle.
  2. **Manager** Tender ne approve kari ne "Open" kare.
  3. **Vendors** open tenders joi shake ane potano bhav (Amount) ane delivery timeline sathe **Bid** (Technical & Commercial proposal) submit kare.
  4. Time puro thay etle Tender "Closed" thai jay.

### Phase 6: Bid Evaluation & Awarding
- **What it does:** Je bids aavi che aenu checking karvu ane ek company ne contract aapvo.
- **Workflow:**
  1. **Procurement Officer** aaveli badhi bids ne check kare ane **100 marks** mathi score aape (Price: 40, Experience: 30, Warranty: 20, Delivery: 10).
  2. Jo koi bid na marks **40 thi ocha** aave to e tarat **Auto-Reject** thai jay.
  3. Officer pass thayeli (shortlisted) bids Manager ne mokle.
  4. **Manager** e shortlisted bids mathi sabthi best (1) bid ne select kari ne **"Approve & Award"** kare. E bid "Winner" bani jay ane baki ni badhi auto-reject thai jay.

### Phase 7: Purchase Order (PO) Management & Delivery
- **What it does:** Winner ne officially saaman mangavvano order aapvo.
- **Workflow:**
  1. **Procurement Officer** winner bid par thi ek Purchase Order (PO) banave jema Tax ane Payment Terms lakheli hoy.
  2. **Manager** e PO ne approve kare.
  3. PO approve thata j **Vendor** ne e dekhase. Vendor saaman mokli de etle system ma **"Dispatched"** mark karse.
  4. Saaman pohchya pachi Vendor **Delivery Proof (Challan/Receipt)** upload kari ne **"Delivered"** mark karse.
  5. Manager/Officer payment clear kari ne PO ne **"Completed & Closed"** mark karse.

### Phase 8: Reporting & Analytics (Future/Final Phase)
- **What it does:** System ni aakhi summary (kharcho, performance).
- **Workflow:** Admin ane Manager mate reports (PDF/Excel) generate thase jema khabar padse ke ketlu budget vpray aiyu, kya vendor nu kam sabthi saru che, ane ketla tenders success thaya.

---
*Aa README file project ni root directory ma save kari che, jethi bhavishya ma koi pan developer ne aakhu architecture tarat samajai jay.*
