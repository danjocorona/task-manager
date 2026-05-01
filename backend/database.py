# Handles the database engine and session lifecycle.
# SQLModel uses SQLAlchemy under the hood, create_engine sets up
# the connection, while get_session is a FastAPI dependency that
# opens a session per request and closes it cleanly when done.

from sqlmodel import SQLModel, create_engine, Session

# SQLite file-based database - stored in the backend folder.
# check_same_thread=False is required for SQLite with FastAPI
# because FastAPI can handle multiple threads.
DATABASE_URL = "sqlite:///./taskmanager.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True to print all SQL queries
)

def create_db_and_tables():
    """
    Create all database tables defined by SQLModel models.
    Called once on application startup in main.py
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    FastAPI dependency - yields a database session for each request
    and guarantees it is closed afterwards, even if an error occurs.

    Usage in a route:
        def my_route(session: Session = Depends(get_session)):
    """
    with Session(engine) as session:
        yield session