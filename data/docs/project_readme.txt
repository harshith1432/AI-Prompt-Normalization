Project: Attendance Monitoring System

Overview:
This project uses cameras at entry gates to capture presence and match students via recognition models. Teachers can review and approve attendance records when needed. A small SQLite database stores consolidated attendance and reports. The system includes an admin UI to view reports and export CSVs. Typical components: camera capture, recognition model, backend api server, database, and teacher approval workflow.

Deployment notes:
- Camera nodes stream snapshots to the processing service.
- Model inference aims for high accuracy while keeping latency low.
- The backend stores raw events, consolidated attendance, and exception logs.
