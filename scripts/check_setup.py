"""
Check Sen2Nal development environment setup.

Run this script to verify all components are working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_python_version():
    """Check Python version is 3.11+"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (need 3.11+)")
        return False


def check_dependencies():
    """Check required packages are installed."""
    print("\n📦 Checking dependencies...")

    required_packages = [
        ("fastapi", "FastAPI"),
        ("streamlit", "Streamlit"),
        ("sqlalchemy", "SQLAlchemy"),
        ("alembic", "Alembic"),
        ("transformers", "Transformers"),
        ("pandas", "Pandas"),
    ]

    all_ok = True
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} (not installed)")
            all_ok = False

    return all_ok


def check_database():
    """Check database connection."""
    print("\n🗄️  Checking database connection...")
    try:
        from src.database.connection import check_db_connection

        if check_db_connection():
            print("   ✅ PostgreSQL connection successful")
            return True
        else:
            print("   ❌ PostgreSQL connection failed")
            print("   💡 Run: docker-compose up -d postgres")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_environment_file():
    """Check .env file exists."""
    print("\n⚙️  Checking environment configuration...")
    env_file = Path(__file__).parent.parent / ".env"

    if env_file.exists():
        print("   ✅ .env file exists")
        return True
    else:
        print("   ⚠️  .env file not found")
        print("   💡 Run: cp .env.example .env")
        return True  # Not critical for Phase 0


def check_migrations():
    """Check migrations status."""
    print("\n🔄 Checking database migrations...")
    try:
        import subprocess
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        if "head" in result.stdout or result.returncode == 0:
            print("   ✅ Migrations are up to date")
            return True
        else:
            print("   ⚠️  Migrations may not be applied")
            print("   💡 Run: alembic upgrade head")
            return False
    except Exception as e:
        print(f"   ⚠️  Could not check migrations: {e}")
        return False


def check_docker():
    """Check Docker is running."""
    print("\n🐳 Checking Docker...")
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("   ✅ Docker is running")

            # Check if postgres container is running
            if "sen2nal-postgres" in result.stdout:
                print("   ✅ PostgreSQL container is running")
            else:
                print("   ⚠️  PostgreSQL container not running")
                print("   💡 Run: docker-compose up -d postgres")
            return True
        else:
            print("   ❌ Docker is not running")
            print("   💡 Start Docker Desktop")
            return False
    except FileNotFoundError:
        print("   ❌ Docker not found")
        print("   💡 Install Docker: https://docs.docker.com/get-docker/")
        return False


def main():
    """Run all checks."""
    print("=" * 80)
    print("🔍 Sen2Nal Development Environment Check")
    print("=" * 80)

    checks = [
        check_python_version(),
        check_dependencies(),
        check_docker(),
        check_environment_file(),
        check_database(),
        check_migrations(),
    ]

    print("\n" + "=" * 80)
    if all(checks):
        print("✅ All checks passed! You're ready to develop.")
        print("\nNext steps:")
        print("  1. Start API:       make run-api")
        print("  2. Start Dashboard: make run-dashboard")
        print("  3. Visit: http://localhost:8501")
    else:
        print("⚠️  Some checks failed. Please review above.")
        print("\nQuick fixes:")
        print("  • Docker:     Start Docker Desktop")
        print("  • Database:   docker-compose up -d postgres")
        print("  • Migrations: alembic upgrade head")
        print("  • Packages:   poetry install")
    print("=" * 80)


if __name__ == "__main__":
    main()
