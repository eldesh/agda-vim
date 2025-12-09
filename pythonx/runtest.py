import unittest

def main():
    suite = unittest.defaultTestLoader.discover(
        "tests", pattern="test_*.py"
    )
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == "__main__":
    main()
