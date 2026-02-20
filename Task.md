# 📦 Project: Operation Ghost Hunter

## 1. The Situation
Our city-wide network of 2,000 solar-powered **Smart Lockers** is haunted. We are losing high-value packages. 

Currently, when a customer drops a package, the locker confirms the drop-off locally. However, due to aggressive power-saving modes and spotty 5G coverage, these lockers go offline for 10–30 minutes at a time. We are seeing "Ghost Packages"—items that exist in a physical locker but have **zero record** in our central Postgres database because the sync failed mid-transmission or the locker rebooted before finishing the handshake.

## 2. Your Starting Point
We have provided a "Baseline MVP" in this repository:
* **Locker (Python/Peewee/SQLite):** A basic edge service that records drops and tries to POST them.
* **Server (Go/Gin/GORM/Postgres):** A central API that receives and stores package data.

**⚠️ WARNING:** The baseline code was written by a summer intern. It works... maybe... sometimes... on a local machine with a perfect connection, but it is architecturally flawed for a distributed system. It uses sequential integer IDs, has no retry logic, and zero data integrity guarantees. Ok honestly we don't even know if this thing runs.

## 3. The Mission
Your task is to refactor this POC into a production-grade synchronization engine. We have a **Hard Audit** scheduled for next week. And we need to perform.

### Core Requirements:
1.  **Zero Data Loss:** If a locker's SQLite DB records a drop-off, that record *must* eventually reach the Postgres DB, even if the locker crashes or the network is dead for 20 minutes.
2.  **Idempotency & Collision Resistance:** We have 2,000 lockers. If two lockers sync at the same time, or one locker sends the same data twice due to a 5G timeout, the central database must remain consistent and duplicate-free.
3.  **The "Last-Mile" Handshake:** Implement a robust sync protocol between the Python edge and the Go core. How do you know the server *actually* saved it before the locker marks it as "Synced"?
4.  **Audit Trail:** Every package must have a verifiable "Chain of Custody" timestamp from the moment the door closed to the moment the server acknowledged the record.

## 4. Technical Constraints
* **Do not change the stack:** Stick with Python/SQLite on the edge and Go/Postgres on the server.
* **Efficiency:** Remember, these are solar-powered. Don't build a sync loop that drains the battery by polling the API every 500ms.
* **The "ID Problem":** You are free (and encouraged) to fix the way we identify packages. Sequential integers in a distributed system are a disaster waiting to happen.

## 5. Evaluation Criteria
We aren't looking at your code; we are looking at your **judgment**. Please don't spend ages working on "perfect code". As you can see by this haphazard, unstructured and unprofesional half AI generated repository, this is not what the test is about. We want to see your **reasoning** as the **lead** of a project thrown into a messy situation. 
* How do you handle a "Partial Write" (Locker dies mid-sync)?
* How do you handle "Clock Drift" between the locker and the server?
* How do you handle "The Missing ACK" (Server saved it, but the locker never heard back)?

---
*Good luck. The couriers are waiting.*