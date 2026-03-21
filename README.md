# 🩺 DoctorFlow

**DoctorFlow** is a high-performance management ecosystem designed for healthcare professionals who need to balance patient care with precise financial control. By integrating clinical workflows with real-time billing and automated subscriptions, DoctorFlow transforms administrative burdens into a streamlined, automated process.

---

## 🚀 Purpose & Core Features

The application stands on three pillars: **Clinical Precision**, **Financial Transparency**, and **Process Automation**.

* **Patient Management:** Full lifecycle tracking of patients, from initial registration to consultation history and recurring appointments.
* **Real-time Financial Dashboard:** Dynamic visualization of revenue metrics, including total billing, average ticket per patient, and revenue forecasting.
* **Automated Billing:** Seamless integration of payments, ensuring that practitioners spend less time on invoices and more time on diagnosis.
* **Secure Access Control:** Robust authentication system with automated redirects based on subscription status and session validation.

---

## 🛠️ Tech Stack

DoctorFlow utilizes a modern, decoupled architecture to ensure scalability and professional-grade performance.

### **Frontend**
* **HTML5 & TailwindCSS:** A utility-first approach for a responsive, clean, and professional medical interface.
* **JavaScript (Vanilla):** High-performance DOM manipulation with **Optimistic UI** updates for instantaneous user actions (like deletions and status changes).

### **Backend**
* **Python + FastAPI:** An asynchronous, high-concurrency framework chosen for its speed and native support for data validation via Pydantic.
* **SQLAlchemy:** Advanced ORM for complex relationship mapping and database integrity.

### **Financial Integration**
* **Stripe API:** Powering the entire payment infrastructure:
    * **Stripe Checkout:** Secure, PCI-compliant payment sessions.
    * **Webhooks:** Real-time synchronization between payment events (subscriptions, renewals, cancellations) and the internal database.

### **Cloud & Infrastructure**
* **Database:** **MySQL** hosted on **AWS RDS**, providing high availability and encrypted storage.
* **Code Hosting:** **Railway**, utilizing automated CI/CD pipelines for seamless deployment from the repository to production.

---

## 🏗️ Architecture & Security

The system is designed to be "Environment Aware," pulling sensitive configurations from secure environment variables.

1.  **Request Handling:** FastAPI manages incoming traffic, validating JWT/Session tokens.
2.  **Data Persistence:** MySQL (via AWS RDS) handles relational data with optimized indexing for fast clinical retrieval.
3.  **External Sync:** Webhooks listen for Stripe events (`whsec`) to automatically grant or revoke access based on payment status.
4.  **Resilient Deletion:** Integrated cleanup protocols that synchronize database deletions with Stripe customer/subscription cancellations.

---

## 🌐 Deployment

The production environment is currently live at:  
🔗 [doctorflow.app.br](https://doctorflow.app.br)

---
