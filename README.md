[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/hLqvXyMi)

**Sports Lending App @ UVA**

This is a Django-based web application designed to support a sports equipment lending system for the University of Virginia. Users can browse an equipment catalog, request items to borrow, return items, submit reviews, and manage collections. The system supports role-based functionality for patrons and librarians, with oversight from Django superusers.

**Overview**

This application facilitates equipment lending among students and staff, where patrons can browse and borrow equipment, librarians can approve or deny requests and monitor overdue items, and anonymous users can view the catalog before logging in. Key interactions such as loan management, librarian approval, item reviews, and item collections are supported with a clean and responsive user interface.

**Features**

📦 Catalog: View, search, and filter available sports equipment.

🔐 Authentication: Google login via Django AllAuth.

📄 Borrow/Return System: Patrons can request items to borrow; librarians approve/deny.

⏰ Loan Duration Control: Librarians set loan duration and suspend users for overdue returns.

💬 Review System: Patrons can review and rate borrowed equipment.

🗂️ Collections: Users can create item collections and request shared access.

🔔 Notifications: Patrons are notified of overdue items or suspensions.

🧑‍💼 Librarian Management: Role requests, access approval, and borrower oversight.

**User Roles**

- Anonymous Users: Can access the application but must log in to interact with the actalog among other functionalities.

- Patrons: Can request to borrow, return, and review equipment.

- Librarians: Can approve/deny borrow requests, manage loans, suspend patrons, and oversee collections.

- Superusers: Django admin-level users with full backend access.

**Team Roles**

Requirements Manager (Amy) – Led the initial feature elicitation process and managed the GitHub issue tracker throughout development.

Testing Manager (Marilyn) – Oversaw testing strategies, ensured test coverage, and organized the final beta testing process.

DevOps Manager (Abhinov) – Handled deployments, repository setup, Heroku integration, and resolved technical infrastructure issues.

Software Architect (Winston) – Designed solutions for mid-semester requirement changes and guided their integration into the project.

Scrum Master (Mauricio) – Kept the team organized, on schedule, and served as the main point of contact with course staff.  

**Deployment**

This app is deployed on Heroku:
👉 [https://sports-gear-lending-at-uva.herokuapp.com/](https://sports-gear-lending-at-uva-cab93fa3d7df.herokuapp.com/)
