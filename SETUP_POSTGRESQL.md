# PostgreSQL Setup Guide for Windows

This guide will walk you through installing PostgreSQL on Windows for the Email Analytics Dashboard project.

## Step 1: Download PostgreSQL

1. Visit the official PostgreSQL download page: https://www.postgresql.org/download/windows/
2. Click on "Download the installer" (this will take you to EnterpriseDB)
3. Download the latest PostgreSQL version for Windows (recommended: PostgreSQL 15 or 16)
4. Choose the Windows x86-64 installer

## Step 2: Install PostgreSQL

1. Run the downloaded installer (.exe file)
2. Click "Next" on the welcome screen
3. Choose installation directory (default is fine: `C:\Program Files\PostgreSQL\16`)
4. Select components to install (keep all defaults checked):
   - PostgreSQL Server
   - pgAdmin 4 (GUI tool)
   - Stack Builder
   - Command Line Tools
5. Choose data directory (default is fine)
6. **Set a password for the postgres superuser** - **REMEMBER THIS PASSWORD!**
   - Example: `postgres123` (use a secure password in production)
7. Set port number (default: `5432`)
8. Set locale (default is fine)
9. Review the summary and click "Next"
10. Click "Next" to begin installation
11. Wait for installation to complete (may take a few minutes)
12. Uncheck "Stack Builder" at the end and click "Finish"

## Step 3: Verify Installation

1. Open Command Prompt (cmd)
2. Navigate to PostgreSQL bin directory:
   ```cmd
   cd "C:\Program Files\PostgreSQL\16\bin"
   ```
3. Test the connection:
   ```cmd
   psql -U postgres
   ```
4. Enter the password you set during installation
5. You should see the PostgreSQL prompt: `postgres=#`
6. Type `\q` to exit

## Step 4: Add PostgreSQL to PATH (Optional but Recommended)

1. Right-click "This PC" or "My Computer" → Properties
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "System variables", find and select "Path"
5. Click "Edit"
6. Click "New"
7. Add: `C:\Program Files\PostgreSQL\16\bin`
8. Click "OK" on all dialogs
9. **Restart Command Prompt** for changes to take effect

Now you can run `psql` from any directory!

## Step 5: Create the Database

1. Open Command Prompt
2. Connect to PostgreSQL:
   ```cmd
   psql -U postgres
   ```
3. Create the database:
   ```sql
   CREATE DATABASE email_analytics;
   ```
4. Verify the database was created:
   ```sql
   \l
   ```
   You should see `email_analytics` in the list
5. Connect to the new database:
   ```sql
   \c email_analytics
   ```
6. Exit psql:
   ```sql
   \q
   ```

## Step 6: Configure Environment Variables for the Project

1. In the `email-analytics-dashboard` folder, create a file named `.env`
2. Add the following content (replace `your_password` with your actual postgres password):
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=email_analytics
   DB_USER=postgres
   DB_PASSWORD=your_password
   ```
3. Save the file

## Troubleshooting

### "psql is not recognized as an internal or external command"
- PostgreSQL bin directory is not in PATH
- Use full path: `"C:\Program Files\PostgreSQL\16\bin\psql" -U postgres`
- Or follow Step 4 to add to PATH

### "password authentication failed for user postgres"
- You entered the wrong password
- Reset password using pgAdmin 4 or reinstall PostgreSQL

### Port 5432 already in use
- Another service is using port 5432
- During installation, choose a different port (e.g., 5433)
- Update `.env` file with the new port

### Connection refused
- PostgreSQL service is not running
- Open Services (Win + R, type `services.msc`)
- Find "postgresql-x64-16" service
- Right-click → Start

## Next Steps

After completing this setup:
1. The database `email_analytics` is ready
2. The scraper will automatically create the `emails` table when first run
3. Continue with the main README.md for project setup instructions
