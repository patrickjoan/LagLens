import sys

from app import LagLensApp


def main():
    """Main entry point for the LagLens application."""
    try:
        app = LagLensApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

