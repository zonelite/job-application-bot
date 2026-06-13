import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import DB_PATH
from database.models import Database
from security import CredentialManager

st.set_page_config(page_title="Job Bot Dashboard", layout="wide")


def main():
    st.title("🤖 Job Application Bot Dashboard")
    st.markdown("---")

    # Initialize database
    db = Database(DB_PATH)
    creds = CredentialManager()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        if st.button("📋 Setup Profile"):
            st.session_state["show_profile"] = True
        
        if st.button("🔄 Run Application Cycle"):
            st.session_state["run_cycle"] = True

    # Main dashboard
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Stats", "📝 Applications", "📧 Email Monitor", "⚙️ Setup"]
    )

    with tab1:
        st.subheader("Application Statistics")
        
        stats = db.get_application_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Applications", stats["total_applications"])
        
        with col2:
            st.metric("Submitted", stats["submitted"])
        
        with col3:
            st.metric("Interviewed", stats["interviewed"])
        
        with col4:
            st.metric("Success Rate", f"{stats['success_rate']}%")
        
        st.markdown("---")
        
        # Applications today
        st.subheader("Today's Applications")
        today_apps = db.get_applications_today()
        
        if today_apps:
            for app in today_apps:
                cols = st.columns([3, 1, 1])
                with cols[0]:
                    st.write(f"**{app.job_title}** @ {app.company}")
                with cols[1]:
                    status_color = {
                        "submitted": "🟢",
                        "pending": "🟡",
                        "rejected": "🔴",
                        "interviewed": "🔵",
                    }
                    st.write(f"{status_color.get(app.status, '⚪')} {app.status}")
                with cols[2]:
                    st.write(app.date_applied[:10])
        else:
            st.info("No applications today yet.")

    with tab2:
        st.subheader("Application History")
        
        # Get last 30 days
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT job_title, company, status, date_applied, url
            FROM applications
            WHERE DATE(date_applied) >= DATE('now', '-30 days')
            ORDER BY date_applied DESC
            """
        )
        apps = cursor.fetchall()
        conn.close()
        
        if apps:
            for app in apps:
                with st.expander(f"{app['job_title']} @ {app['company']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Status:** {app['status']}")
                        st.write(f"**Applied:** {app['date_applied']}")
                    with col2:
                        st.write(f"**URL:** [Link]({app['url']})")
        else:
            st.info("No applications in the last 30 days.")

    with tab3:
        st.subheader("Email Response Monitor")
        
        if st.button("Check Emails Now"):
            from monitoring import EmailMonitor
            
            monitor = EmailMonitor()
            emails = monitor.get_recent_emails(days=7)
            statuses = monitor.parse_application_status(emails)
            
            st.success(f"Found {len(emails)} emails from last 7 days")
            
            if statuses:
                st.subheader("Detected Application Responses")
                for status in statuses:
                    st.write(
                        f"**From:** {status['sender']}\n"
                        f"**Subject:** {status['subject']}\n"
                        f"**Type:** {status['status_type']} (confidence: {status['confidence']:.0%})"
                    )
            else:
                st.info("No application responses detected.")

    with tab4:
        st.subheader("Profile Setup")
        
        with st.form("profile_form"):
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            email = st.text_input("Email Address")
            phone = st.text_input("Phone Number")
            
            if st.form_submit_button("Save Profile"):
                creds.save_credentials(
                    "user_profile",
                    {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                    },
                )
                st.success("✅ Profile saved successfully!")


if __name__ == "__main__":
    main()
