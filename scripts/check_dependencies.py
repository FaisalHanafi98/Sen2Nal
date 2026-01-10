"""
Comprehensive dependency checker for Sen2Nal.
Checks all requirements before running the application.
"""

import sys
import subprocess
from pathlib import Path

# Color codes for Windows
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print section header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    """Print info message."""
    print(f"   {text}")

def check_python_version():
    """Check Python version."""
    print_header("1️⃣  PYTHON VERSION")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major >= 3 and version.minor >= 11:
        print_success(f"Python {version_str}")
        return True
    else:
        print_error(f"Python {version_str} (need 3.11+)")
        print_info("Download: https://www.python.org/downloads/")
        return False

def check_pip():
    """Check pip is available."""
    print_header("2️⃣  PIP PACKAGE MANAGER")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"pip is available: {version}")
            return True
        else:
            print_error("pip is not working properly")
            return False
    except Exception as e:
        print_error(f"pip check failed: {e}")
        return False

def check_poetry():
    """Check if Poetry is installed and accessible."""
    print_header("3️⃣  POETRY")

    # Try poetry command directly
    try:
        result = subprocess.run(
            ["poetry", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success(f"Poetry (command): {result.stdout.strip()}")
            return True, "command"
    except FileNotFoundError:
        pass

    # Try python -m poetry
    try:
        result = subprocess.run(
            [sys.executable, "-m", "poetry", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success(f"Poetry (module): {result.stdout.strip()}")
            print_warning("Poetry not in PATH - use: python -m poetry")
            return True, "module"
    except Exception:
        pass

    print_error("Poetry not installed")
    print_info("Install: pip install poetry")
    return False, None

def check_core_packages():
    """Check core Python packages."""
    print_header("4️⃣  CORE PYTHON PACKAGES")

    packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "streamlit": "Streamlit",
        "sqlalchemy": "SQLAlchemy",
        "alembic": "Alembic",
        "psycopg2": "psycopg2-binary",
        "pydantic": "Pydantic",
        "pydantic_settings": "Pydantic Settings",
    }

    results = {}
    for module, name in packages.items():
        try:
            __import__(module)
            print_success(f"{name}")
            results[name] = True
        except ImportError:
            print_error(f"{name} - NOT INSTALLED")
            results[name] = False

    return all(results.values()), results

def check_ml_packages():
    """Check ML/NLP packages."""
    print_header("5️⃣  ML/NLP PACKAGES")

    packages = {
        "transformers": "Transformers (HuggingFace)",
        "torch": "PyTorch",
        "xgboost": "XGBoost",
        "sklearn": "scikit-learn",
        "shap": "SHAP",
        "pandas": "Pandas",
        "numpy": "NumPy",
    }

    results = {}
    for module, name in packages.items():
        try:
            __import__(module)
            print_success(f"{name}")
            results[name] = True
        except ImportError:
            print_warning(f"{name} - NOT INSTALLED (needed for Phase 2)")
            results[name] = False

    # ML packages are optional for Phase 0
    return True, results

def check_data_packages():
    """Check data processing packages."""
    print_header("6️⃣  DATA PROCESSING PACKAGES")

    packages = {
        "requests": "Requests",
        "aiohttp": "aiohttp",
        "praw": "PRAW (Reddit)",
        "yfinance": "yfinance",
        "bs4": "BeautifulSoup4",
        "lxml": "lxml",
        "boto3": "boto3 (AWS)",
        "apscheduler": "APScheduler",
    }

    results = {}
    for module, name in packages.items():
        try:
            __import__(module)
            print_success(f"{name}")
            results[name] = True
        except ImportError:
            print_warning(f"{name} - NOT INSTALLED (needed for Phase 1)")
            results[name] = False

    # Data packages are optional for Phase 0
    return True, results

def check_dev_packages():
    """Check development packages."""
    print_header("7️⃣  DEVELOPMENT PACKAGES")

    packages = {
        "pytest": "pytest",
        "black": "Black",
        "ruff": "Ruff",
        "mypy": "MyPy",
        "isort": "isort",
        "playwright": "Playwright",
    }

    results = {}
    for module, name in packages.items():
        try:
            __import__(module)
            print_success(f"{name}")
            results[name] = True
        except ImportError:
            print_warning(f"{name} - NOT INSTALLED (dev tool)")
            results[name] = False

    # Dev packages are optional
    return True, results

def check_docker():
    """Check Docker."""
    print_header("8️⃣  DOCKER")

    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success(f"Docker: {result.stdout.strip()}")

            # Check if Docker is running
            try:
                ps_result = subprocess.run(
                    ["docker", "ps"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if ps_result.returncode == 0:
                    print_success("Docker daemon is running")

                    # Check for sen2nal-postgres container
                    if "sen2nal-postgres" in ps_result.stdout:
                        print_success("PostgreSQL container is running")
                    else:
                        print_warning("PostgreSQL container not running")
                        print_info("Start: docker-compose up -d postgres")

                    return True
                else:
                    print_warning("Docker daemon not running")
                    print_info("Start Docker Desktop")
                    return False
            except Exception as e:
                print_warning(f"Cannot check Docker status: {e}")
                return True
        else:
            print_error("Docker not working properly")
            return False
    except FileNotFoundError:
        print_error("Docker not installed")
        print_info("Download: https://docs.docker.com/get-docker/")
        return False
    except Exception as e:
        print_error(f"Docker check failed: {e}")
        return False

def check_docker_compose():
    """Check Docker Compose."""
    print_header("9️⃣  DOCKER COMPOSE")

    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success(f"Docker Compose: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    # Try docker compose (v2)
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success(f"Docker Compose V2: {result.stdout.strip()}")
            print_info("Note: Use 'docker compose' instead of 'docker-compose'")
            return True
    except Exception:
        pass

    print_error("Docker Compose not installed")
    print_info("Included with Docker Desktop")
    return False

def check_environment_file():
    """Check .env file."""
    print_header("🔟 ENVIRONMENT CONFIGURATION")

    env_file = Path(__file__).parent.parent / ".env"
    env_example = Path(__file__).parent.parent / ".env.example"

    if env_file.exists():
        print_success(".env file exists")
        return True
    elif env_example.exists():
        print_warning(".env file not found")
        print_info("Create: cp .env.example .env")
        print_info("(Not critical for Phase 0)")
        return True
    else:
        print_error("Neither .env nor .env.example found")
        return False

def check_database_connection():
    """Check database connection."""
    print_header("1️⃣1️⃣  DATABASE CONNECTION")

    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from src.database.connection import check_db_connection

        if check_db_connection():
            print_success("PostgreSQL connection successful")
            return True
        else:
            print_warning("PostgreSQL connection failed")
            print_info("1. Start: docker-compose up -d postgres")
            print_info("2. Wait 10 seconds for PostgreSQL to initialize")
            print_info("3. Check .env DATABASE_URL setting")
            return False
    except ImportError as e:
        print_warning(f"Cannot test database (missing dependencies)")
        print_info(f"Error: {e}")
        return False
    except Exception as e:
        print_warning(f"Database check failed: {e}")
        print_info("This is OK if you haven't started PostgreSQL yet")
        return False

def print_summary(checks):
    """Print summary of all checks."""
    print_header("📊 SUMMARY")

    total = len(checks)
    passed = sum(1 for v in checks.values() if v)
    failed = total - passed

    print(f"Total Checks: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    if failed > 0:
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")

    print("\n" + "=" * 80 + "\n")

    if all(checks.values()):
        print_success("ALL CHECKS PASSED! ✨")
        print("\n🚀 You're ready to start development!\n")
        print("Next steps:")
        print("  1. python -m poetry install")
        print("  2. docker-compose up -d postgres")
        print("  3. python -m poetry run alembic upgrade head")
        print("  4. python -m poetry run uvicorn src.api.main:app --reload")
        print("  5. python -m poetry run streamlit run src/dashboard/app.py")
    else:
        print_warning("SOME CHECKS FAILED")
        print("\n📝 Action Items:\n")

        if not checks.get("Python"):
            print("  • Install Python 3.11+")
        if not checks.get("Poetry"):
            print("  • Install Poetry: pip install poetry")
        if not checks.get("Core Packages"):
            print("  • Install packages: python -m poetry install")
        if not checks.get("Docker"):
            print("  • Install Docker Desktop")
        if not checks.get("Database"):
            print("  • Start PostgreSQL: docker-compose up -d postgres")

        print("\n💡 For Phase 0, you mainly need:")
        print("  ✓ Python 3.11+")
        print("  ✓ Poetry (or use: python -m poetry)")
        print("  ✓ Core packages (FastAPI, Streamlit, SQLAlchemy)")
        print("  ✓ Docker + PostgreSQL")
        print("\n  Other packages can be installed later as needed.")

    print("\n" + "=" * 80)

def main():
    """Run all checks."""
    print(f"\n{Colors.BOLD}{'=' * 80}")
    print(f"🔍 Sen2Nal Dependency Checker")
    print(f"{'=' * 80}{Colors.RESET}\n")

    checks = {}

    # Critical checks (required for Phase 0)
    checks["Python"] = check_python_version()
    checks["pip"] = check_pip()
    poetry_ok, poetry_type = check_poetry()
    checks["Poetry"] = poetry_ok

    core_ok, _ = check_core_packages()
    checks["Core Packages"] = core_ok

    checks["Docker"] = check_docker()
    checks["Docker Compose"] = check_docker_compose()
    checks["Environment"] = check_environment_file()
    checks["Database"] = check_database_connection()

    # Optional checks (for future phases)
    ml_ok, _ = check_ml_packages()
    data_ok, _ = check_data_packages()
    dev_ok, _ = check_dev_packages()

    # Print summary
    print_summary(checks)

    # Return exit code
    critical_checks = ["Python", "pip", "Poetry", "Docker"]
    if all(checks.get(c, False) for c in critical_checks):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
